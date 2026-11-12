import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.wrong_dates import purge_old_wrongs, wrong_date_bounds
from app.models.category import Category
from app.models.exam import Exam
from app.models.practice import UserAnswer, WrongQuestion, QuestionMark
from app.models.question import Question, QuestionOption
from app.models.user import User
from app.schemas.practice import AnswerResult, AnswerSubmit, PracticeStats, MarkUpdate, MarkOut

router = APIRouter(prefix="/api/practice", tags=["刷题"])


@router.post("/submit", response_model=AnswerResult)
def submit_answer(
    answer: AnswerSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Question).filter(Question.id == answer.question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")

    correct_options = db.query(QuestionOption).filter(
        QuestionOption.question_id == q.id,
        QuestionOption.is_correct == 1,
    ).order_by(QuestionOption.sort).all()
    correct_answer = "".join(sorted(o.label.strip().upper() for o in correct_options))

    user_labels = "".join(sorted(re.sub(r"[^A-Z]", "", answer.user_answer.upper())))
    is_correct = user_labels == correct_answer

    db.add(UserAnswer(
        user_id=current_user.id,
        exam_id=answer.exam_id,
        question_id=q.id,
        user_answer=answer.user_answer,
        is_correct=1 if is_correct else 0,
        score=q.score if is_correct else 0,
    ))

    if not is_correct:
        existing = db.query(WrongQuestion).filter(
            WrongQuestion.user_id == current_user.id,
            WrongQuestion.question_id == q.id,
        ).first()
        source = "exam" if answer.exam_id else "practice"
        if existing:
            existing.wrong_count += 1
            existing.last_wrong_time = func.now()
            existing.last_answer = answer.user_answer
            existing.mastered = 0
            existing.source = source
            existing.exam_id = answer.exam_id
        else:
            db.add(WrongQuestion(
                user_id=current_user.id,
                question_id=q.id,
                wrong_count=1,
                last_answer=answer.user_answer,
                source=source,
                exam_id=answer.exam_id,
            ))
    else:
        existing = db.query(WrongQuestion).filter(
            WrongQuestion.user_id == current_user.id,
            WrongQuestion.question_id == q.id,
        ).first()
        if existing:
            existing.mastered = 1

    db.commit()

    return AnswerResult(
        is_correct=is_correct,
        correct_answer=correct_answer,
        analysis=q.analysis,
        score=q.score if is_correct else 0,
    )


def _category_scope(db: Session, category_id: int | None):
    """分类筛选包含子分类：选“内燃专业”时，其下所有模块的题都算"""
    if not category_id:
        return None
    ids = {category_id}
    for child in db.query(Category).filter(Category.parent_id == category_id).all():
        ids.add(child.id)
    return ids


def _wrong_query(
    db: Session,
    user_id: int,
    category_id: int | None,
    qtype: str | None,
    keyword: str | None,
    status: str,
    start_date: date | None = None,
    end_date: date | None = None,
    source: str | None = None,
):
    query = (
        db.query(WrongQuestion)
        .join(Question, Question.id == WrongQuestion.question_id)
        .filter(WrongQuestion.user_id == user_id)
    )
    if source == "practice":
        query = query.filter(WrongQuestion.source == "practice")
    elif source == "exam":
        query = query.filter(WrongQuestion.source == "exam")
    if status == "pending":
        query = query.filter(WrongQuestion.mastered == 0)
    elif status == "mastered":
        query = query.filter(WrongQuestion.mastered == 1)
    bounds = wrong_date_bounds(start_date, end_date)
    if bounds is None:
        # 开始日期晚于结束日期：刻意返回空结果
        query = query.filter(WrongQuestion.id == -1)
    else:
        start_utc, end_utc = bounds
        query = query.filter(
            WrongQuestion.last_wrong_time >= start_utc,
            WrongQuestion.last_wrong_time < end_utc,
        )
    scope = _category_scope(db, category_id)
    if scope:
        query = query.filter(Question.category_id.in_(scope))
    if qtype:
        query = query.filter(Question.type == qtype)
    if keyword:
        query = query.filter(Question.content.like(f"%{keyword.strip()}%"))
    return query


def _category_names(db: Session):
    return {c.id: c.name for c in db.query(Category).all()}


def _question_payload(db: Session, q: Question):
    options = db.query(QuestionOption).filter(
        QuestionOption.question_id == q.id
    ).order_by(QuestionOption.sort).all()
    correct = "".join(sorted(
        o.label.strip().upper() for o in options if o.is_correct == 1
    ))
    return {
        "id": q.id,
        "content": q.content,
        "image": q.image,
        "type": q.type,
        "score": float(q.score or 1),
        "analysis": q.analysis,
        "options": [
            {"id": o.id, "label": o.label, "content": o.content, "is_correct": o.is_correct}
            for o in options
        ],
        "correct_answer": correct,
    }


def _mark_payload(mark: QuestionMark):
    return {
        "question_id": mark.question_id,
        "is_favorite": bool(mark.is_favorite),
        "note": mark.note or "",
        "annotation": mark.annotation or "",
        "updated_at": mark.updated_at,
    }


def _parse_question_ids(value: str):
    ids = []
    for part in (value or "").split(","):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    return ids


def _mark_map(db: Session, user_id: int, question_ids: list[int]):
    """批量取收藏状态，错题列表卡片可以直接显示星标"""
    if not question_ids:
        return {}
    marks = db.query(QuestionMark).filter(
        QuestionMark.user_id == user_id,
        QuestionMark.question_id.in_(question_ids),
    ).all()
    return {int(m.question_id): bool(m.is_favorite) for m in marks}


def _exam_title_map(db: Session, exam_ids: list[int]):
    if not exam_ids:
        return {}
    rows = db.query(Exam).filter(Exam.id.in_(exam_ids)).all()
    return {int(e.id): e.title for e in rows}


@router.get("/marks", response_model=list[MarkOut])
def list_marks(
    question_ids: str = Query("", description="逗号分隔的题目ID，通常传当前这一批题"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ids = _parse_question_ids(question_ids)
    if not ids:
        return []
    marks = db.query(QuestionMark).filter(
        QuestionMark.user_id == current_user.id,
        QuestionMark.question_id.in_(ids),
    ).all()
    return [_mark_payload(m) for m in marks]


@router.put("/marks/{question_id}", response_model=MarkOut)
def save_mark(
    question_id: int,
    payload: MarkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")

    mark = db.query(QuestionMark).filter(
        QuestionMark.user_id == current_user.id,
        QuestionMark.question_id == question_id,
    ).first()
    if not mark:
        mark = QuestionMark(user_id=current_user.id, question_id=question_id)
        db.add(mark)

    data = payload.model_dump(exclude_unset=True)
    if "is_favorite" in data:
        mark.is_favorite = 1 if data["is_favorite"] else 0
    if "note" in data:
        mark.note = (data["note"] or "").strip() or None
    if "annotation" in data:
        mark.annotation = data["annotation"] or None

    db.commit()
    db.refresh(mark)
    return _mark_payload(mark)


@router.get("/favorites")
def list_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(QuestionMark)
        .join(Question, Question.id == QuestionMark.question_id)
        .filter(
            QuestionMark.user_id == current_user.id,
            QuestionMark.is_favorite == 1,
            Question.status == 1,
        )
    )
    total = query.count()
    rows = query.order_by(QuestionMark.updated_at.desc(), QuestionMark.id.desc()) \
        .offset((page - 1) * page_size).limit(page_size).all()
    names = _category_names(db)
    items = []
    for mark in rows:
        q = db.query(Question).filter(Question.id == mark.question_id).first()
        if not q:
            continue
        payload = _question_payload(db, q)
        payload["category_name"] = names.get(q.category_id, "未分类")
        payload["note"] = mark.note or ""
        payload["annotation"] = mark.annotation or ""
        items.append(payload)
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/favorites/questions")
def favorite_questions_for_practice(
    count: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """收藏复习按收藏时间倒序取题，学员可接着上次位置继续"""
    query = (
        db.query(QuestionMark)
        .join(Question, Question.id == QuestionMark.question_id)
        .filter(
            QuestionMark.user_id == current_user.id,
            QuestionMark.is_favorite == 1,
            Question.status == 1,
        )
    )
    rows = query.order_by(QuestionMark.updated_at.desc(), QuestionMark.id.desc()) \
        .offset(offset).limit(count).all()
    result = []
    for mark in rows:
        q = db.query(Question).filter(Question.id == mark.question_id).first()
        if not q:
            continue
        payload = _question_payload(db, q)
        payload["note"] = mark.note or ""
        payload["annotation"] = mark.annotation or ""
        result.append(payload)
    return result


@router.get("/search")
def search_questions(
    keyword: str = Query(..., min_length=1, description="题干或解析关键词"),
    category_id: int | None = Query(None, description="分类ID，自动包含子分类"),
    type: str | None = Query(None, description="题型"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """学员搜题：按题干/解析关键词搜索，结果可直接查看答案与解析"""
    text = keyword.strip()
    if not text:
        raise HTTPException(status_code=400, detail="请输入搜索关键词")

    query = db.query(Question).filter(Question.status == 1)
    scope = _category_scope(db, category_id)
    if scope:
        query = query.filter(Question.category_id.in_(scope))
    if type:
        query = query.filter(Question.type == type)
    query = query.filter(or_(
        Question.content.contains(text),
        Question.analysis.contains(text),
    ))

    total = query.count()
    rows = query.order_by(Question.id.asc()) \
        .offset((page - 1) * page_size).limit(page_size).all()
    names = _category_names(db)
    items = []
    for q in rows:
        payload = _question_payload(db, q)
        payload["category_name"] = names.get(q.category_id, "未分类")
        items.append(payload)
    return {"total": total, "page": page, "page_size": page_size, "keyword": text, "items": items}


@router.get("/wrong/list")
def list_wrong_questions(
    category_id: int | None = Query(None, description="分类ID，自动包含子分类"),
    type: str | None = Query(None, description="题型"),
    keyword: str | None = Query(None, description="题干关键词"),
    status: str = Query("pending", description="pending 待复习 / mastered 已掌握 / all 全部"),
    sort: str = Query("recent", description="recent 最近错的在前 / count 错得多的在前"),
    start_date: date | None = Query(None, description="开始日期（本地日期 YYYY-MM-DD）"),
    end_date: date | None = Query(None, description="结束日期（本地日期 YYYY-MM-DD）"),
    source: str | None = Query(None, description="来源：practice 刷题 / exam 考试，留空为全部"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    purged = purge_old_wrongs(db, current_user.id)
    query = _wrong_query(
        db, current_user.id, category_id, type, keyword, status, start_date, end_date, source
    )
    total = query.count()

    if sort == "count":
        query = query.order_by(WrongQuestion.wrong_count.desc(), WrongQuestion.last_wrong_time.desc())
    else:
        query = query.order_by(WrongQuestion.last_wrong_time.desc(), WrongQuestion.wrong_count.desc())

    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    names = _category_names(db)
    marks = _mark_map(db, current_user.id, [int(w.question_id) for w in rows])
    exams = _exam_title_map(db, [int(w.exam_id) for w in rows if w.exam_id])

    items = []
    for w in rows:
        q = db.query(Question).filter(Question.id == w.question_id).first()
        if not q:
            continue
        items.append({
            "id": w.id,
            "question_id": w.question_id,
            "wrong_count": w.wrong_count,
            "last_wrong_time": w.last_wrong_time,
            "last_answer": w.last_answer,
            "mastered": w.mastered,
            "source": w.source or "practice",
            "exam_id": w.exam_id,
            "exam_title": exams.get(int(w.exam_id)) if w.exam_id else None,
            "is_favorite": marks.get(int(w.question_id), False),
            "content": q.content,
            "type": q.type,
            "category_id": q.category_id,
            "category_name": names.get(q.category_id, "未分类"),
        })

    pending_query = db.query(WrongQuestion).filter(
        WrongQuestion.user_id == current_user.id, WrongQuestion.mastered == 0
    )
    if source == "practice":
        pending_query = pending_query.filter(WrongQuestion.source == "practice")
    elif source == "exam":
        pending_query = pending_query.filter(WrongQuestion.source == "exam")
    pending_total = pending_query.count()
    mastered_total = db.query(WrongQuestion).filter(
        WrongQuestion.user_id == current_user.id, WrongQuestion.mastered == 1
    ).count()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pending_total": pending_total,
        "mastered_total": mastered_total,
        "purged": purged,
        "retention_days": 10,
        "items": items,
    }


@router.get("/wrong/questions")
def wrong_questions_for_practice(
    category_id: int | None = Query(None),
    type: str | None = Query(None),
    keyword: str | None = Query(None),
    status: str = Query("pending"),
    sort: str = Query("count"),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    source: str | None = Query(None, description="来源：practice 刷题 / exam 考试"),
    count: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """按当前错题筛选条件抽题，用于“重做这些错题”"""
    purge_old_wrongs(db, current_user.id)
    query = _wrong_query(
        db, current_user.id, category_id, type, keyword, status, start_date, end_date, source
    )
    if sort == "count":
        query = query.order_by(WrongQuestion.wrong_count.desc(), WrongQuestion.id.asc())
    else:
        query = query.order_by(WrongQuestion.last_wrong_time.desc(), WrongQuestion.id.asc())

    rows = query.offset(offset).limit(count).all()
    result = []
    for w in rows:
        q = db.query(Question).filter(Question.id == w.question_id).first()
        if q:
            payload = _question_payload(db, q)
            payload["wrong_count"] = w.wrong_count
            result.append(payload)
    return result


@router.get("/wrong/{question_id}/detail")
def wrong_detail(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """错题详情：题干、选项、正确答案、解析、上次答错的答案"""
    purge_old_wrongs(db, current_user.id)
    w = db.query(WrongQuestion).filter(
        WrongQuestion.user_id == current_user.id,
        WrongQuestion.question_id == question_id,
    ).first()
    if not w:
        raise HTTPException(status_code=404, detail="错题不存在")
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")

    detail = _question_payload(db, q)
    names = _category_names(db)
    mark = db.query(QuestionMark).filter(
        QuestionMark.user_id == current_user.id,
        QuestionMark.question_id == question_id,
    ).first()
    detail.update({
        "wrong_count": w.wrong_count,
        "last_wrong_time": w.last_wrong_time,
        "last_answer": w.last_answer,
        "mastered": w.mastered,
        "source": w.source or "practice",
        "exam_id": w.exam_id,
        "exam_title": _exam_title_map(db, [int(w.exam_id)]).get(int(w.exam_id)) if w.exam_id else None,
        "is_favorite": bool(mark.is_favorite) if mark else False,
        "category_name": names.get(q.category_id, "未分类"),
    })
    return detail


@router.post("/wrong/{question_id}/master")
def mark_mastered(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    w = db.query(WrongQuestion).filter(
        WrongQuestion.user_id == current_user.id,
        WrongQuestion.question_id == question_id,
    ).first()
    if not w:
        raise HTTPException(status_code=404, detail="错题不存在")

    w.mastered = 1
    db.commit()
    return {"success": True, "message": "已标记为掌握"}


@router.delete("/wrong/{question_id}")
def delete_wrong(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    w = db.query(WrongQuestion).filter(
        WrongQuestion.user_id == current_user.id,
        WrongQuestion.question_id == question_id,
    ).first()
    if not w:
        raise HTTPException(status_code=404, detail="错题不存在")

    db.delete(w)
    db.commit()
    return {"success": True, "message": "已移出错题本"}


@router.get("/stats", response_model=PracticeStats)
def get_practice_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = db.query(UserAnswer).filter(UserAnswer.user_id == current_user.id).count()
    correct = db.query(UserAnswer).filter(
        UserAnswer.user_id == current_user.id,
        UserAnswer.is_correct == 1,
    ).count()
    wrong = total - correct
    accuracy = round(correct / total * 100, 1) if total > 0 else 0

    return PracticeStats(
        total_answered=total,
        correct_count=correct,
        wrong_count=wrong,
        accuracy=accuracy,
    )
