# -*- coding: utf-8 -*-
from datetime import date, datetime, time, timedelta, timezone

# 错题保留窗口：滚动 10 天；更早的记录从数据库删除
WRONG_RETENTION_DAYS = 10
LOCAL_TZ = timezone(timedelta(hours=8))


def local_today() -> date:
    return datetime.now(LOCAL_TZ).date()


def min_selectable_date() -> date:
    """日期筛选最早可选：今天往前 9 天，共 10 个自然日。"""
    return local_today() - timedelta(days=WRONG_RETENTION_DAYS - 1)


def max_selectable_date() -> date:
    return local_today()


def retention_cutoff_utc() -> datetime:
    """返回 UTC naive 时间，用于和 SQLite CURRENT_TIMESTAMP 比较。"""
    return datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=WRONG_RETENTION_DAYS)


def wrong_date_bounds(start_date: date | None, end_date: date | None):
    """把本地日期范围转换成 UTC naive 的 [开始, 结束) 边界。"""
    earliest = min_selectable_date()
    latest = max_selectable_date()
    start_day = max(start_date or earliest, earliest)
    end_day = min(end_date or latest, latest)
    if start_day > end_day:
        return None
    start_local = datetime.combine(start_day, time.min, tzinfo=LOCAL_TZ)
    end_local = datetime.combine(end_day + timedelta(days=1), time.min, tzinfo=LOCAL_TZ)
    return (
        start_local.astimezone(timezone.utc).replace(tzinfo=None),
        end_local.astimezone(timezone.utc).replace(tzinfo=None),
    )


def purge_old_wrongs(db, user_id: int) -> int:
    """删除该用户超过保留窗口的错题记录，返回删除数量。"""
    from app.models.practice import WrongQuestion

    cutoff = retention_cutoff_utc()
    query = db.query(WrongQuestion).filter(
        WrongQuestion.user_id == user_id,
        WrongQuestion.last_wrong_time < cutoff,
    )
    count = query.count()
    if count:
        query.delete(synchronize_session=False)
        db.commit()
    return count
