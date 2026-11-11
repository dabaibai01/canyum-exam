import mimetypes

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.api.upload import delete_local_file, resolve_local_file
from app.core.database import get_db
from app.core.deps import require_admin
from app.models.media import Video, Book
from app.schemas.media import VideoOut, VideoCreate, BookOut, BookCreate

router = APIRouter(prefix="/api/media", tags=["媒体"])

# ========== 视频 ==========

@router.get("/videos", response_model=list[VideoOut])
def list_videos(
    category_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Video).filter(Video.status == 1)
    if category_id:
        query = query.filter(Video.category_id == category_id)
    videos = query.order_by(Video.sort).offset((page - 1) * page_size).limit(page_size).all()
    return videos

@router.get("/videos/{video_id}", response_model=VideoOut)
def get_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    return video

@router.post("/videos", response_model=VideoOut, dependencies=[Depends(require_admin)])
def create_video(video_in: VideoCreate, db: Session = Depends(get_db)):
    video = Video(**video_in.model_dump())
    db.add(video)
    db.commit()
    db.refresh(video)
    return video

@router.put("/videos/{video_id}", response_model=VideoOut, dependencies=[Depends(require_admin)])
def update_video(video_id: int, video_in: VideoCreate, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    old_url = video.video_url
    for key, value in video_in.model_dump().items():
        setattr(video, key, value)
    db.commit()
    db.refresh(video)
    if old_url != video.video_url:
        delete_local_file(old_url)
    return video

@router.delete("/videos/{video_id}", dependencies=[Depends(require_admin)])
def delete_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    old_url = video.video_url
    db.delete(video)
    db.commit()
    delete_local_file(old_url)
    return {"message": "删除成功"}

# ========== 书籍 ==========

@router.get("/books", response_model=list[BookOut])
def list_books(
    category_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Book).filter(Book.status == 1)
    if category_id:
        query = query.filter(Book.category_id == category_id)
    books = query.order_by(Book.sort).offset((page - 1) * page_size).limit(page_size).all()
    return books

@router.get("/books/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    return book

@router.post("/books", response_model=BookOut, dependencies=[Depends(require_admin)])
def create_book(book_in: BookCreate, db: Session = Depends(get_db)):
    book = Book(**book_in.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book

@router.get("/books/{book_id}/file")
def open_book_file(book_id: int, db: Session = Depends(get_db)):
    """公开打开书籍文件：本地文件按书名返回，外链直接跳转。"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book or not book.file_url:
        raise HTTPException(status_code=404, detail="书籍文件不存在")

    local = resolve_local_file(book.file_url)
    if local:
        media_type = mimetypes.guess_type(str(local))[0] or "application/octet-stream"
        return FileResponse(
            str(local),
            media_type=media_type,
            filename=f"{book.title}{local.suffix}",
            content_disposition_type="inline",
        )
    return RedirectResponse(book.file_url, status_code=307)

@router.put("/books/{book_id}", response_model=BookOut, dependencies=[Depends(require_admin)])
def update_book(book_id: int, book_in: BookCreate, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    old_url = book.file_url
    for key, value in book_in.model_dump().items():
        setattr(book, key, value)
    db.commit()
    db.refresh(book)
    if old_url != book.file_url:
        delete_local_file(old_url)
    return book

@router.delete("/books/{book_id}", dependencies=[Depends(require_admin)])
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    old_url = book.file_url
    db.delete(book)
    db.commit()
    delete_local_file(old_url)
    return {"message": "删除成功"}
