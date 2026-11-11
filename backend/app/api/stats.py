from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.category import Category
from app.models.exam import Exam
from app.models.practice import UserAnswer
from app.models.question import Question
from app.models.user import User

router = APIRouter(prefix="/api/stats", tags=["统计"])

TYPE_LABELS = {"single": "单选题", "multiple": "多选题", "judge": "判断题"}

# 数据库里的 answer_time 由 SQLite CURRENT_TIMESTAMP 写入，是 UTC 时间；
# 看板按北京时间展示和分天统计，查询时统一 +8 小时。
LOCAL_TZ_HOURS = 8


def _local_time(column):
    return func.datetime(column, f"+{LOCAL_TZ_HOURS} hours")


def _parse_day(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式应为 YYYY-MM-DD")


def _collect_user_stats(
    db: Session,
    scope: str,
    start_date: str | None,
    end_date: str | None,
    keyword: str | None,
    category_id: int | None,
    page: int,
    page_size: int,
):
    """按日期、专业统计每个账号的答题量、答对数和正确率。

    scope="practice"：只统计刷题（UserAnswer.exam_id 为空）。
    scope="exam"：只统计在线考试/自己组卷（UserAnswer.exam_id 非空），并带出考试名称。
    两种口径都包含管理员账号，管理员也可以刷题和参加考试。
    """
    today = datetime.now().date()
    start_day = _parse_day(start_date, today - timedelta(days=6))
    end_day = _parse_day(end_date, today)
    if end_day < start_day:
        raise HTTPException(status_code=400, detail="结束日期不能早于开始日期")

    start_dt = datetime(start_day.year, start_day.month, start_day.day)
    end_dt = datetime(end_day.year, end_day.month, end_day.day) + timedelta(days=1)

    columns = [
        UserAnswer.user_id,
        func.date(_local_time(UserAnswer.answer_time)).label("day"),
        Question.category_id,
        func.count(UserAnswer.id).label("answered"),
        func.sum(UserAnswer.is_correct).label("correct"),
    ]
    if scope == "exam":
        columns.extend([
            UserAnswer.exam_id.label("exam_id"),
            Exam.title.label("exam_title"),
        ])

    query = (
        db.query(*columns)
        .join(Question, UserAnswer.question_id == Question.id)
        .join(User, UserAnswer.user_id == User.id)
        .filter(
            _local_time(UserAnswer.answer_time) >= start_dt,
            _local_time(UserAnswer.answer_time) < end_dt,
        )
    )
    if scope == "exam":
        query = query.outerjoin(Exam, UserAnswer.exam_id == Exam.id).filter(
            UserAnswer.exam_id.is_not(None)
        )
    else:
        query = query.filter(UserAnswer.exam_id.is_(None))

    if keyword and keyword.strip():
        kw = keyword.strip()
        query = query.filter(
            or_(
                User.username.contains(kw),
                User.real_name.contains(kw),
                User.department.contains(kw),
            )
        )

    rows = query.all()

    users = {u.id: u for u in db.query(User).all()}
    categories = {
        c.id: c for c in db.query(Category).filter(Category.type == "question").all()
    }
    prof_filter = None
    if category_id and category_id > 0:
        cat = categories.get(category_id)
        prof_filter = (cat.parent_id or cat.id) if cat else category_id

    groups: dict[tuple, dict] = {}
    for row in rows:
        user_id, day, q_category_id, answered, correct = row[:5]
        exam_id = row[5] if scope == "exam" else None
        exam_title = row[6] if scope == "exam" else None

        cat = categories.get(q_category_id)
        if not cat:
            continue
        prof_id = cat.parent_id or cat.id
        if prof_filter and int(prof_id) != int(prof_filter):
            continue

        uid = int(user_id)
        key = (uid, str(day), int(prof_id), exam_id if scope == "exam" else None)
        item = groups.setdefault(key, {
            "user_id": uid,
            "date": str(day),
            "profession_id": int(prof_id),
            "profession": categories.get(prof_id).name if categories.get(prof_id) else "未分类",
            "answered": 0,
            "correct": 0,
            "exam_id": exam_id,
            "exam_title": exam_title,
        })
        item["answered"] += int(answered or 0)
        item["correct"] += int(correct or 0)

    items = []
    for item in groups.values():
        u = users.get(item["user_id"])
        item["real_name"] = (u.real_name or u.username) if u else "已删除用户"
        item["username"] = u.username if u else ""
        item["department"] = u.department if u else ""
        item["position"] = u.position if u else ""
        item["role"] = u.role if u else ""
        item["is_admin"] = 1 if u and u.role == "admin" else 0
        item["accuracy"] = round(item["correct"] * 100 / item["answered"], 1) if item["answered"] else 0.0
        if scope == "exam" and not item.get("exam_title"):
            item["exam_title"] = "已删除考试"
        items.append(item)

    items.sort(key=lambda x: (x["date"], x["answered"], x["user_id"]), reverse=True)
    total = len(items)
    total_answered = sum(i["answered"] for i in items)
    total_correct = sum(i["correct"] for i in items)
    summary = {
        "all_users": len(users),
        "active_users": len({i["user_id"] for i in items}),
        "answered": total_answered,
        "correct": total_correct,
        "accuracy": round(total_correct * 100 / total_answered, 1) if total_answered else 0.0,
        "days": len({i["date"] for i in items}),
        "exam_count": len({i["exam_id"] for i in items}) if scope == "exam" else 0,
    }

    start = (page - 1) * page_size
    return {
        "summary": summary,
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items[start:start + page_size],
    }


@router.get("/practice-users", dependencies=[Depends(require_admin)])
def practice_users(
    start_date: str | None = Query(None, description="开始日期 YYYY-MM-DD，默认近 7 天"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD，默认今天"),
    keyword: str | None = Query(None, description="姓名/用户名/部门关键词"),
    category_id: int | None = Query(None, description="专业大类 ID，0 表示全部"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """管理端：刷题统计，包含管理员账号。"""
    return _collect_user_stats(
        db, "practice", start_date, end_date, keyword, category_id, page, page_size
    )


@router.get("/exam-users", dependencies=[Depends(require_admin)])
def exam_users(
    start_date: str | None = Query(None, description="开始日期 YYYY-MM-DD，默认近 7 天"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD，默认今天"),
    keyword: str | None = Query(None, description="姓名/用户名/部门关键词"),
    category_id: int | None = Query(None, description="专业大类 ID，0 表示全部"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """管理端：考试统计，包含在线考试和自己组卷，包含管理员账号。"""
    return _collect_user_stats(
        db, "exam", start_date, end_date, keyword, category_id, page, page_size
    )


@router.get("/dashboard", dependencies=[Depends(require_admin)])
def dashboard(db: Session = Depends(get_db)):
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)

    total_questions = db.query(func.count(Question.id)).filter(Question.status == 1).scalar() or 0
    total_users = db.query(func.count(User.id)).filter(User.role == "user").scalar() or 0
    total_exams = db.query(func.count(Exam.id)).filter(Exam.created_by.is_(None)).scalar() or 0

    ongoing_exams = db.query(func.count(Exam.id)).filter(
        Exam.created_by.is_(None),
        Exam.status == 1,
        or_(Exam.start_time.is_(None), Exam.start_time <= now),
        or_(Exam.end_time.is_(None), Exam.end_time >= now),
    ).scalar() or 0

    today_answers = db.query(func.count(UserAnswer.id)).filter(
        _local_time(UserAnswer.answer_time) >= today_start
    ).scalar() or 0
    today_correct = db.query(func.count(UserAnswer.id)).filter(
        _local_time(UserAnswer.answer_time) >= today_start,
        UserAnswer.is_correct == 1,
    ).scalar() or 0

    total_answers = db.query(func.count(UserAnswer.id)).scalar() or 0
    total_correct = db.query(func.count(UserAnswer.id)).filter(UserAnswer.is_correct == 1).scalar() or 0

    # 题型分布
    type_stats = []
    rows = db.query(Question.type, func.count(Question.id)).filter(
        Question.status == 1
    ).group_by(Question.type).all()
    for type_code, count in rows:
        type_stats.append({"name": TYPE_LABELS.get(type_code, type_code), "value": count})

    # 专业大类题量（父分类汇总子分类；只统计真正有子模块的专业大类）
    category_stats = []
    parents = db.query(Category).filter(
        Category.parent_id == 0, Category.type == "question"
    ).order_by(Category.sort).all()
    for parent in parents:
        child_ids = [
            c.id for c in db.query(Category).filter(Category.parent_id == parent.id).all()
        ]
        if not child_ids:
            # 没有子模块的是早期的测试分类，不计入专业分布
            continue
        cnt = db.query(func.count(Question.id)).filter(
            Question.status == 1,
            Question.category_id.in_([parent.id] + child_ids),
        ).scalar() or 0
        category_stats.append({"name": parent.name, "value": cnt})
    category_stats.sort(key=lambda x: x["value"], reverse=True)

    # 最近 7 天答题趋势
    daily_stats = []
    for i in range(6, -1, -1):
        day_start = today_start - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        answered = db.query(func.count(UserAnswer.id)).filter(
            _local_time(UserAnswer.answer_time) >= day_start,
            _local_time(UserAnswer.answer_time) < day_end,
        ).scalar() or 0
        correct = db.query(func.count(UserAnswer.id)).filter(
            _local_time(UserAnswer.answer_time) >= day_start,
            _local_time(UserAnswer.answer_time) < day_end,
            UserAnswer.is_correct == 1,
        ).scalar() or 0
        active_users = db.query(func.count(func.distinct(UserAnswer.user_id))).filter(
            _local_time(UserAnswer.answer_time) >= day_start,
            _local_time(UserAnswer.answer_time) < day_end,
        ).scalar() or 0
        daily_stats.append({
            "date": day_start.strftime("%m-%d"),
            "answered": answered,
            "correct": correct,
            "users": active_users,
        })

    return {
        "total_questions": total_questions,
        "total_users": total_users,
        "total_exams": total_exams,
        "ongoing_exams": ongoing_exams,
        "today_answers": today_answers,
        "today_correct": today_correct,
        "today_correct_rate": round(today_correct * 100 / today_answers, 1) if today_answers else 0.0,
        "total_answers": total_answers,
        "total_correct_rate": round(total_correct * 100 / total_answers, 1) if total_answers else 0.0,
        "type_stats": type_stats,
        "category_stats": category_stats,
        "daily_stats": daily_stats,
    }
