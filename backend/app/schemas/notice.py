from pydantic import BaseModel
from datetime import datetime


class NoticeOut(BaseModel):
    id: int
    title: str
    content: str
    status: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class NoticeCreate(BaseModel):
    title: str
    content: str
    status: int = 0


class NoticeUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    status: int | None = None
