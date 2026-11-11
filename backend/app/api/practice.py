import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.wrong_dates import purge_old_wrongs, wrong_date_bounds
from app.models.category import Category
from app.models.practice import UserAnswer, WrongQuestion
from app.models.question import Question, QuestionOption
from app.models.user import User
from app.schemas.practice import AnswerResult, AnswerSubmit, PracticeStats

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
        if existing:
            existing.wrong_count += 1
            existing.last_wrong_time = func.now()
            existing.last_answer = answer.user_answer
            existing.mastered = 0
        else:
            db.add(WrongQuestion(
                user_id=current_user.id,
                question_id=q.id,
                wrong_count=1,
                last_answer=answer.user_answer,
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
):
    query = (
        db.query(WrongQuestion)
        .join(Question, Question.id == WrongQuestion.question_id)
        .filter(WrongQuestion.user_id == user_id)
    )
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


@router.get("/wrong/list")
def list_wrong_questions(
    category_id: int | None = Query(None, description="分类ID，自动包含子分类"),
    type: str | None = Query(None, description="题型"),
    keyword: str | None = Query(None, description="题干关键词"),
    status: str = Query("pending", description="pending 待复习 / mastered 已掌握 / all 全部"),
    sort: str = Query("recent", description="recent 最近错的在前 / count 错得多的在前"),
    start_date: date | None = Query(None, description="开始日期（本地日期 YYYY-MM-DD）"),
    end_date: date | None = Query(None, description="结束日期（本地日期 YYYY-MM-DD）"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    purged = purge_old_wrongs(db, current_user.id)
    query = _wrong_query(
        db, current_user.id, category_id, type, keyword, status, start_date, end_date
    )
    total = query.count()

    if sort == "count":
        query = query.order_by(WrongQuestion.wrong_count.desc(), WrongQuestion.last_wrong_time.desc())
    else:
        query = query.order_by(WrongQuestion.last_wrong_time.desc(), WrongQuestion.wrong_count.desc())

    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    names = _category_names(db)

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
            "content": q.content,
            "type": q.type,
            "category_id": q.category_id,
            "category_name": names.get(q.category_id, "未分类"),
        })

    pending_total = db.query(WrongQuestion).filter(
        WrongQuestion.user_id == current_user.id, WrongQuestion.mastered == 0
    ).count()
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
    count: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """按当前错题筛选条件抽题，用于“重做这些错题”"""
    purge_old_wrongs(db, current_user.id)
    query = _wrong_query(
        db, current_user.id, category_id, type, keyword, status, start_date, end_date
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
    detail.update({
        "wrong_count": w.wrong_count,
        "last_wrong_time": w.last_wrong_time,
        "last_answer": w.last_answer,
        "mastered": w.mastered,
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
