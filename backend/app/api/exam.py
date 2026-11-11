import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.core.wrong_dates import purge_old_wrongs, wrong_date_bounds
from app.models.category import Category
from app.models.exam import Exam, ExamAttempt, ExamQuestion
from app.models.practice import UserAnswer, WrongQuestion
from app.models.question import Question, QuestionOption
from app.models.user import User
from app.schemas.exam import ComposeItem, ExamCreate, ExamOut, SelfCompose
from app.schemas.question import OptionOut, QuestionOut

router = APIRouter(prefix="/api/exams", tags=["考试"])

TYPE_LABELS = {"single": "单选题", "multiple": "多选题", "judge": "判断题"}


def _question_pool(db: Session, category_id: int | None, qtype: str | None = None):
    """题库池：按分类（父分类自动包含子分类）和题型过滤，只取启用的题"""
    query = db.query(Question).filter(Question.status == 1)
    if category_id and category_id > 0:
        child_ids = [
            c.id for c in db.query(Category).filter(Category.parent_id == category_id).all()
        ]
        query = query.filter(Question.category_id.in_([category_id] + child_ids))
    if qtype:
        query = query.filter(Question.type == qtype)
    return query


def _available_counts(db: Session, category_id: int | None) -> dict:
    return {
        "single": _question_pool(db, category_id, "single").count(),
        "multiple": _question_pool(db, category_id, "multiple").count(),
        "judge": _question_pool(db, category_id, "judge").count(),
    }


def _rows_from_compose(db: Session, category_id: int | None, compose) -> list[tuple[int, float]]:
    """按题型数量随机抽题，返回 [(question_id, score), ...]"""
    items = [c for c in compose if c.count and c.count > 0]
    if not items:
        raise HTTPException(status_code=400, detail="请至少选择一种题型并设置数量")

    rows: list[tuple[int, float]] = []
    for item in items:
        if item.type not in TYPE_LABELS:
            raise HTTPException(status_code=400, detail=f"不支持的题型：{item.type}")
        if item.score is None or item.score <= 0:
            raise HTTPException(status_code=400, detail=f"{TYPE_LABELS[item.type]}的分值必须大于 0")
        pool_count = _question_pool(db, category_id, item.type).count()
        if item.count > pool_count:
            raise HTTPException(
                status_code=400,
                detail=f"{TYPE_LABELS[item.type]}数量不足：需要 {item.count} 道，题库中只有 {pool_count} 道",
            )
        picked = (
            _question_pool(db, category_id, item.type)
            .order_by(func.random())
            .limit(item.count)
            .all()
        )
        for q in picked:
            rows.append((q.id, float(item.score)))

    return rows


def _rows_from_ids(db: Session, question_ids: list[int]) -> list[tuple[int, float]]:
    rows = []
    for qid in question_ids:
        q = db.query(Question).filter(Question.id == qid).first()
        if q:
            rows.append((q.id, float(q.score or 1.0)))
    return rows


def _apply_rows(db: Session, exam: Exam, rows: list[tuple[int, float]]):
    exam.question_count = len(rows)
    exam.total_score = round(sum(s for _, s in rows), 1)
    for i, (qid, score) in enumerate(rows):
        db.add(ExamQuestion(exam_id=exam.id, question_id=qid, score=score, sort=i + 1))


def _my_attempts(db: Session, exam_id: int, user_id: int) -> list:
    return (
        db.query(ExamAttempt)
        .filter(ExamAttempt.exam_id == exam_id, ExamAttempt.user_id == user_id)
        .order_by(ExamAttempt.submitted_at.desc(), ExamAttempt.id.desc())
        .all()
    )


def _retake_state(exam: Exam, attempts: list) -> dict:
    """能不能再考、还剩几次。retake_limit=0 且允许重考时表示不限次数"""
    used = len(attempts)
    if used == 0:
        can_take, remaining = True, (None if exam.retake_limit == 0 else 1 + int(exam.retake_limit))
    elif not exam.allow_retake:
        can_take, remaining = False, 0
    elif int(exam.retake_limit or 0) == 0:
        can_take, remaining = True, None
    else:
        allowed_total = 1 + int(exam.retake_limit)
        remaining = max(allowed_total - used, 0)
        can_take = remaining > 0
    best = max([float(a.score or 0) for a in attempts], default=None)
    passed = any(a.passed for a in attempts)
    return {
        "used": used,
        "can_take": can_take,
        "remaining": remaining,
        "best_score": best,
        "passed": passed,
    }


def _ensure_exam_access(exam: Exam, user: User):
    """学员自测卷只有本人能看；管理员创建的公共考试所有人可见"""
    if exam.created_by and int(exam.created_by) != int(user.id) and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权访问这场自测卷")


@router.get("/list", response_model=list[ExamOut])
def list_exams(
    status: int | None = Query(None, description="状态：0草稿/1发布/2结束"),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = db.query(Exam).filter(Exam.created_by.is_(None))
    if status is not None:
        query = query.filter(Exam.status == status)
    exams = query.order_by(Exam.created_at.desc()).all()
    return exams

@router.get("/available")
def available_questions(
    category_id: int = Query(0, description="0 表示全部题目，父分类自动包含子分类"),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """各题型当前可抽题量，管理员组卷和学员自测都用这个接口"""
    counts = _available_counts(db, category_id)
    counts["total"] = counts["single"] + counts["multiple"] + counts["judge"]
    return counts


def _wrong_rows(db: Session, user_id: int, data: SelfCompose) -> list[tuple[int, float]]:
    """从错题本抽题：按当前筛选条件取错得最多/最近的题"""
    query = (
        db.query(WrongQuestion, Question)
        .join(Question, WrongQuestion.question_id == Question.id)
        .filter(WrongQuestion.user_id == user_id, Question.status == 1)
    )
    if data.wrong_status == "pending":
        query = query.filter(WrongQuestion.mastered == 0)
    elif data.wrong_status == "mastered":
        query = query.filter(WrongQuestion.mastered == 1)
    if data.wrong_type:
        query = query.filter(Question.type == data.wrong_type)
    if data.category_id and data.category_id > 0:
        child_ids = [
            c.id for c in db.query(Category).filter(Category.parent_id == data.category_id).all()
        ]
        query = query.filter(Question.category_id.in_([data.category_id] + child_ids))
    bounds = wrong_date_bounds(data.start_date, data.end_date)
    if bounds is None:
        query = query.filter(WrongQuestion.id == -1)
    else:
        start_utc, end_utc = bounds
        query = query.filter(
            WrongQuestion.last_wrong_time >= start_utc,
            WrongQuestion.last_wrong_time < end_utc,
        )
    if data.wrong_sort == "recent":
        query = query.order_by(WrongQuestion.last_wrong_time.desc(), WrongQuestion.id.desc())
    else:
        query = query.order_by(WrongQuestion.wrong_count.desc(), WrongQuestion.last_wrong_time.desc())
    limit = min(max(int(data.count or 0), 1), 100)
    score = min(max(float(data.score or 1.0), 0.5), 10.0)
    rows = query.limit(limit).all()
    return [(int(item.question_id), round(score, 1)) for item, _question in rows]


@router.post("/self-compose", response_model=ExamOut)
def create_self_exam(
    data: SelfCompose,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """学员自测组卷：source=bank 按题型从题库抽题；source=wrong 只抽错题"""
    if data.source == "wrong":
        purge_old_wrongs(db, current_user.id)
        rows = _wrong_rows(db, current_user.id, data)
        if not rows:
            raise HTTPException(status_code=400, detail="当前筛选条件下没有错题，先去刷题积累错题吧")
        default_title = f"错题自测卷 · {datetime.now().strftime('%m-%d %H:%M')}"
        description = "学员从错题本自建的专项自测卷"
    else:
        items = [i for i in data.compose if i.count and i.count > 0]
        if not items:
            raise HTTPException(status_code=400, detail="请至少设置一种题型和数量")
        if sum(i.count for i in items) > 100:
            raise HTTPException(status_code=400, detail="自测卷一次最多 100 题")
        compose = [ComposeItem(type=i.type, count=i.count, score=1.0) for i in items]
        rows = _rows_from_compose(db, data.category_id, compose)
        default_title = f"自测卷 · {datetime.now().strftime('%m-%d %H:%M')}"
        description = "学员自建的题库自测卷"

    title = (data.title or "").strip() or default_title
    exam = Exam(
        title=title[:200],
        description=description,
        category_id=data.category_id,
        total_score=0,
        duration=min(max(int(data.duration or 30), 5), 180),
        question_count=0,
        pass_score=0,
        status=1,
        allow_retake=1,
        retake_limit=0,
        created_by=current_user.id,
    )
    db.add(exam)
    db.flush()
    _apply_rows(db, exam, rows)
    exam.pass_score = round(float(exam.total_score or 0) * 0.6, 1)
    db.commit()
    db.refresh(exam)
    return exam


@router.get("/my-exams")
def my_exams(
    status: int | None = Query(1, description="默认只返回已发布的考试"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """学员视角：管理员发布的公共考试 + 自己创建的自测卷"""
    query = db.query(Exam).filter(
        or_(Exam.created_by.is_(None), Exam.created_by == current_user.id)
    )
    if status is not None:
        query = query.filter(Exam.status == status)
    exams = query.order_by(Exam.created_at.desc()).all()

    items = []
    for exam in exams:
        base = ExamOut.model_validate(exam).model_dump()
        attempts = _my_attempts(db, exam.id, current_user.id)
        base.update(_retake_state(exam, attempts))
        items.append(base)
    return items

@router.get("/my-attempts")
def my_attempts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """我的全部考试成绩记录"""
    exam_titles = {e.id: e.title for e in db.query(Exam).all()}
    rows = (
        db.query(ExamAttempt)
        .filter(ExamAttempt.user_id == current_user.id)
        .order_by(ExamAttempt.submitted_at.desc(), ExamAttempt.id.desc())
        .all()
    )
    return [
        {
            "id": a.id,
            "exam_id": a.exam_id,
            "exam_title": exam_titles.get(int(a.exam_id), "已删除的考试"),
            "score": float(a.score or 0),
            "total_score": float(a.total_score or 0),
            "correct_count": a.correct_count,
            "answered_count": a.answered_count,
            "question_count": a.question_count,
            "passed": bool(a.passed),
            "submitted_at": a.submitted_at,
        }
        for a in rows
    ]

@router.get("/{exam_id}/attempts")
def exam_attempts(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """某场考试：我的历史成绩 + 重考资格"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    attempts = _my_attempts(db, exam_id, current_user.id)
    state = _retake_state(exam, attempts)
    state["records"] = [
        {
            "id": a.id,
            "score": float(a.score or 0),
            "total_score": float(a.total_score or 0),
            "correct_count": a.correct_count,
            "answered_count": a.answered_count,
            "passed": bool(a.passed),
            "submitted_at": a.submitted_at,
        }
        for a in attempts
    ]
    return state

@router.get("/{exam_id}", response_model=ExamOut)
def get_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    _ensure_exam_access(exam, current_user)
    return exam

@router.get("/{exam_id}/questions", response_model=list[QuestionOut])
def get_exam_questions(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    _ensure_exam_access(exam, current_user)

    exam_questions = db.query(ExamQuestion).filter(
        ExamQuestion.exam_id == exam_id
    ).order_by(ExamQuestion.sort).all()

    # 卷内不下发正确答案，避免答题时从接口直接拿到答案
    is_admin = current_user.role == "admin"
    result = []
    for eq in exam_questions:
        q = db.query(Question).filter(Question.id == eq.question_id).first()
        if q:
            q_data = QuestionOut.model_validate(q).model_dump()
            if not is_admin:
                # 考试答题阶段不下发解析，避免解析里直接写出答案
                q_data["analysis"] = None
            options = db.query(QuestionOption).filter(
                QuestionOption.question_id == q.id
            ).order_by(QuestionOption.sort).all()
            q_data["options"] = [
                {
                    "id": o.id,
                    "label": o.label,
                    "content": o.content,
                    "is_correct": o.is_correct if is_admin else 0,
                    "sort": o.sort,
                }
                for o in options
            ]
            q_data["score"] = eq.score
            result.append(q_data)

    return result

@router.post("/", response_model=ExamOut)
def create_exam(
    exam_in: ExamCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    exam_data = exam_in.model_dump(exclude={"question_ids", "compose"})
    exam = Exam(**exam_data)
    db.add(exam)
    db.flush()

    if exam_in.compose:
        rows = _rows_from_compose(db, exam_in.category_id, exam_in.compose)
    elif exam_in.question_ids:
        rows = _rows_from_ids(db, exam_in.question_ids)
    else:
        rows = []

    _apply_rows(db, exam, rows)

    db.commit()
    db.refresh(exam)
    return exam

@router.put("/{exam_id}", response_model=ExamOut)
def update_exam(
    exam_id: int,
    exam_in: ExamCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    exam_data = exam_in.model_dump(exclude={"question_ids", "compose", "total_score"})
    for key, value in exam_data.items():
        setattr(exam, key, value)

    # 未传 question_ids / compose 表示不动已有题目（避免编辑基本信息时把题目清空）
    if exam_in.compose:
        rows = _rows_from_compose(db, exam_in.category_id, exam_in.compose)
        db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam_id).delete()
        _apply_rows(db, exam, rows)
    elif exam_in.question_ids is not None:
        # 已在卷内的题目沿用原分值，避免编辑时把分题型分值冲掉
        old_scores = {
            eq.question_id: float(eq.score or 1.0)
            for eq in db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam_id).all()
        }
        rows = []
        for qid in exam_in.question_ids:
            q = db.query(Question).filter(Question.id == qid).first()
            if q:
                rows.append((q.id, old_scores.get(qid, float(q.score or 1.0))))
        db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam_id).delete()
        _apply_rows(db, exam, rows)

    db.commit()
    db.refresh(exam)
    return exam

@router.delete("/{exam_id}")
def delete_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam_id).delete()
    db.query(ExamAttempt).filter(ExamAttempt.exam_id == exam_id).delete()
    db.query(UserAnswer).filter(UserAnswer.exam_id == exam_id).delete()
    db.delete(exam)
    db.commit()
    return {"message": "删除成功"}

@router.get("/{exam_id}/results")
def exam_results(
    exam_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """管理端：某场考试的所有学员成绩"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    rows = (
        db.query(ExamAttempt)
        .filter(ExamAttempt.exam_id == exam_id)
        .order_by(ExamAttempt.score.desc(), ExamAttempt.submitted_at.desc())
        .all()
    )
    users = {u.id: u for u in db.query(User).all()}
    items = []
    for a in rows:
        u = users.get(int(a.user_id))
        items.append({
            "id": a.id,
            "user_id": a.user_id,
            "real_name": (u.real_name or u.username) if u else "已删除用户",
            "username": u.username if u else "",
            "score": float(a.score or 0),
            "total_score": float(a.total_score or 0),
            "correct_count": a.correct_count,
            "answered_count": a.answered_count,
            "passed": bool(a.passed),
            "submitted_at": a.submitted_at,
        })

    scores = [i["score"] for i in items]
    passed = sum(1 for i in items if i["passed"])
    return {
        "exam_id": exam_id,
        "exam_title": exam.title,
        "total_score": float(exam.total_score or 0),
        "pass_score": float(exam.pass_score or 0),
        "participants": len({i["user_id"] for i in items}),
        "attempts": len(items),
        "passed": passed,
        "pass_rate": round(passed * 100 / len(items), 1) if items else 0.0,
        "avg_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
        "items": items,
    }


@router.post("/{exam_id}/submit")
def submit_exam(
    exam_id: int,
    answers: list[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    _ensure_exam_access(exam, current_user)

    if exam.status != 1:
        raise HTTPException(status_code=403, detail="这场考试当前不接受作答")

    now = datetime.now()
    if exam.start_time and now < exam.start_time:
        raise HTTPException(status_code=403, detail="考试还未开始")
    if exam.end_time and now > exam.end_time:
        raise HTTPException(status_code=403, detail="考试已结束")

    attempts = _my_attempts(db, exam_id, current_user.id)
    state = _retake_state(exam, attempts)
    if not state["can_take"]:
        if attempts and not exam.allow_retake:
            raise HTTPException(status_code=403, detail="本场考试不允许重考，你已经参加过")
        raise HTTPException(status_code=403, detail="重考次数已用完")

    # 只认本场考试的题，同一题重复提交以最后一次为准
    exam_questions = {
        eq.question_id: float(eq.score or 1.0)
        for eq in db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam_id).all()
    }
    answer_map: dict[int, str] = {}
    for ans in answers:
        try:
            qid = int(ans.get("question_id"))
        except (TypeError, ValueError):
            continue
        if qid in exam_questions:
            answer_map[qid] = str(ans.get("user_answer", "")).strip().upper()

    total_score = 0.0
    correct_count = 0

    for qid, user_answer in answer_map.items():
        q = db.query(Question).filter(Question.id == qid).first()
        if not q:
            continue

        correct_options = db.query(QuestionOption).filter(
            QuestionOption.question_id == qid,
            QuestionOption.is_correct == 1
        ).all()
        correct_answer = "".join(sorted(o.label for o in correct_options))

        # 多选题顺序不影响判分：取字母后排序比较
        normalized = "".join(sorted(re.sub(r"[^A-Z]", "", user_answer)))
        is_correct = normalized == correct_answer
        question_score = exam_questions[qid]
        score = question_score if is_correct else 0

        db.add(UserAnswer(
            user_id=current_user.id,
            exam_id=exam_id,
            question_id=qid,
            user_answer=user_answer,
            is_correct=1 if is_correct else 0,
            score=score
        ))

        total_score += score
        if is_correct:
            correct_count += 1

    db.commit()

    is_passed = total_score >= float(exam.pass_score or 0)

    db.add(ExamAttempt(
        exam_id=exam_id,
        user_id=current_user.id,
        score=total_score,
        total_score=float(exam.total_score or 0),
        correct_count=correct_count,
        question_count=int(exam.question_count or 0),
        answered_count=len(answer_map),
        passed=1 if is_passed else 0,
    ))

    db.commit()

    return {
        "exam_id": exam_id,
        "total_score": total_score,
        "correct_count": correct_count,
        "wrong_count": len(answer_map) - correct_count,
        "is_passed": is_passed,
        "pass_score": exam.pass_score,
        "attempts_used": len(attempts) + 1,
        "remaining": None
        if (int(exam.retake_limit or 0) == 0 and exam.allow_retake)
        else max(1 + int(exam.retake_limit or 0) - (len(attempts) + 1), 0),
        "can_take_again": bool(exam.allow_retake)
        and (
            int(exam.retake_limit or 0) == 0
            or len(attempts) + 1 < 1 + int(exam.retake_limit or 0)
        ),
    }
