from pydantic import BaseModel
from datetime import datetime

class VideoOut(BaseModel):
    id: int
    title: str
    description: str | None
    category_id: int | None
    video_url: str
    cover_image: str | None
    duration: int | None
    sort: int
    status: int
    created_at: datetime

    class Config:
        from_attributes = True

class VideoCreate(BaseModel):
    title: str
    description: str | None = None
    category_id: int | None = None
    video_url: str
    cover_image: str | None = None
    duration: int | None = None
    sort: int = 0

class BookOut(BaseModel):
    id: int
    title: str
    author: str | None
    description: str | None
    category_id: int | None
    cover_image: str | None
    file_url: str | None
    sort: int
    status: int
    created_at: datetime

    class Config:
        from_attributes = True

class BookCreate(BaseModel):
    title: str
    author: str | None = None
    description: str | None = None
    category_id: int | None = None
    cover_image: str | None = None
    file_url: str | None = None
    sort: int = 0
