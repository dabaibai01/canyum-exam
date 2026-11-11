from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_admin
from app.models.notice import Notice
from app.schemas.notice import NoticeOut, NoticeCreate, NoticeUpdate

router = APIRouter(prefix="/api/notices", tags=["公告"])


@router.get("/home", response_model=list[NoticeOut])
def home_notices(limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)):
    """学员端首页：只返回已发布的公告，按更新时间倒序"""
    return (
        db.query(Notice)
        .filter(Notice.status == 1)
        .order_by(Notice.updated_at.desc(), Notice.id.desc())
        .limit(limit)
        .all()
    )


@router.get("/list")
def list_notices(
    keyword: str | None = Query(None),
    status: int | None = Query(None, description="0 草稿 / 1 已发布，不传则全部"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Notice)
    if status is not None:
        query = query.filter(Notice.status == status)
    if keyword:
        query = query.filter(Notice.title.like(f"%{keyword.strip()}%"))
    total = query.count()
    rows = (
        query.order_by(Notice.updated_at.desc(), Notice.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [NoticeOut.model_validate(r).model_dump() for r in rows],
    }


@router.get("/{notice_id}", response_model=NoticeOut)
def get_notice(notice_id: int, db: Session = Depends(get_db)):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="公告不存在")
    return notice


@router.post("", response_model=NoticeOut, dependencies=[Depends(require_admin)])
@router.post("/", response_model=NoticeOut, dependencies=[Depends(require_admin)])
def create_notice(
    payload: NoticeCreate = Body(...),
    db: Session = Depends(get_db)
):
    if not payload.title.strip() or not payload.content.strip():
        raise HTTPException(status_code=400, detail="标题和内容不能为空")
    notice = Notice(
        title=payload.title.strip(),
        content=payload.content.strip(),
        status=1 if payload.status == 1 else 0,
    )
    db.add(notice)
    db.commit()
    db.refresh(notice)
    return notice


@router.put("/{notice_id}", response_model=NoticeOut, dependencies=[Depends(require_admin)])
def update_notice(
    notice_id: int,
    payload: NoticeUpdate = Body(...),
    db: Session = Depends(get_db)
):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="公告不存在")

    data = payload.model_dump(exclude_unset=True)
    if "title" in data:
        if not (data["title"] or "").strip():
            raise HTTPException(status_code=400, detail="标题不能为空")
        notice.title = data["title"].strip()
    if "content" in data:
        if not (data["content"] or "").strip():
            raise HTTPException(status_code=400, detail="内容不能为空")
        notice.content = data["content"].strip()
    if "status" in data:
        notice.status = 1 if data["status"] == 1 else 0

    db.commit()
    db.refresh(notice)
    return notice


@router.delete("/{notice_id}", dependencies=[Depends(require_admin)])
def delete_notice(notice_id: int, db: Session = Depends(get_db)):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="公告不存在")
    db.delete(notice)
    db.commit()
    return {"message": "已删除"}
