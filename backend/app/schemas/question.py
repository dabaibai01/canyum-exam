from pydantic import BaseModel
from datetime import datetime

class CategoryOut(BaseModel):
    id: int
    name: str
    parent_id: int
    type: str
    sort: int
    status: int
    # 该分类下的题目数量（父分类会汇总其子分类）
    question_count: int = 0

    class Config:
        from_attributes = True

class CategoryCreate(BaseModel):
    name: str
    parent_id: int = 0
    type: str = "question"
    sort: int = 0
    status: int = 1

class OptionOut(BaseModel):
    id: int
    label: str
    content: str
    is_correct: int
    sort: int

    class Config:
        from_attributes = True

class OptionCreate(BaseModel):
    label: str
    content: str
    is_correct: int = 0
    sort: int = 0

class QuestionOut(BaseModel):
    id: int
    category_id: int
    type: str
    content: str
    image: str | None
    analysis: str | None
    difficulty: int
    score: float
    status: int
    created_at: datetime
    options: list[OptionOut] = []

    class Config:
        from_attributes = True

class QuestionCreate(BaseModel):
    category_id: int
    type: str
    content: str
    image: str | None = None
    analysis: str | None = None
    difficulty: int = 1
    score: float = 1.0
    options: list[OptionCreate]

class QuestionPageOut(BaseModel):
    total: int
    items: list[QuestionOut]
