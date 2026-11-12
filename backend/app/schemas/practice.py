from pydantic import BaseModel
from datetime import datetime

class AnswerSubmit(BaseModel):
    question_id: int
    user_answer: str
    exam_id: int | None = None

class AnswerResult(BaseModel):
    is_correct: bool
    correct_answer: str
    analysis: str | None
    score: float

class WrongQuestionOut(BaseModel):
    id: int
    question_id: int
    wrong_count: int
    last_wrong_time: datetime
    mastered: int
    question_content: str | None = None
    question_type: str | None = None

    class Config:
        from_attributes = True

class PracticeStats(BaseModel):
    total_answered: int
    correct_count: int
    wrong_count: int
    accuracy: float


class MarkUpdate(BaseModel):
    is_favorite: bool | None = None
    note: str | None = None
    annotation: str | None = None


class MarkOut(BaseModel):
    question_id: int
    is_favorite: bool
    note: str | None = None
    annotation: str | None = None
    updated_at: datetime | None = None
