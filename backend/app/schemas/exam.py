from pydantic import BaseModel
from datetime import date, datetime

class ExamOut(BaseModel):
    id: int
    title: str
    description: str | None
    category_id: int | None
    total_score: float
    duration: int | None
    start_time: datetime | None
    end_time: datetime | None
    question_count: int
    pass_score: float
    status: int
    allow_retake: int = 0
    retake_limit: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

class ComposeItem(BaseModel):
    """按题型随机抽题的配置：抽多少道、每题多少分"""
    type: str
    count: int = 0
    score: float = 1.0

class ExamCreate(BaseModel):
    title: str
    description: str | None = None
    category_id: int | None = None
    total_score: float = 100.0
    duration: int | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    pass_score: float = 60.0
    status: int = 0
    allow_retake: int = 0
    retake_limit: int = 0
    # 手动选题：显式传入题目 ID 列表；不传（None）表示不改动已有题目
    question_ids: list[int] | None = None
    # 随机抽题：按题型抽指定数量并单独设分
    compose: list[ComposeItem] | None = None

class SelfComposeItem(BaseModel):
    """学员自测卷：按题型抽题"""
    type: str
    count: int = 0

class SelfCompose(BaseModel):
    """学员自己组卷。source=bank 从题库抽题；source=wrong 只抽错题；source=favorite 只抽收藏题"""
    source: str = "bank"
    category_id: int | None = None
    compose: list[SelfComposeItem] = []
    # 错题/收藏题组卷时使用：抽多少道、每题分值、状态、排序
    count: int = 20
    score: float = 1.0
    wrong_type: str | None = None
    wrong_status: str = "pending"
    wrong_sort: str = "count"
    wrong_source: str | None = None
    favorite_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    duration: int = 30
    title: str | None = None

class ExamResult(BaseModel):
    exam_id: int
    user_id: int
    total_score: float
    correct_count: int
    wrong_count: int
    is_passed: bool
    start_time: datetime
    submit_time: datetime
