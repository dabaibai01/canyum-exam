from sqlalchemy import Column, BigInteger, Integer, String, Text, SmallInteger, DateTime, Numeric, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base

class UserAnswer(Base):
    __tablename__ = "user_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    exam_id = Column(BigInteger, index=True)
    question_id = Column(BigInteger, nullable=False, index=True)
    user_answer = Column(Text)
    is_correct = Column(SmallInteger, default=0)
    score = Column(Numeric(5, 1), default=0)
    answer_time = Column(DateTime, server_default=func.now())

class WrongQuestion(Base):
    __tablename__ = "wrong_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    question_id = Column(BigInteger, nullable=False)
    wrong_count = Column(Integer, default=1)
    last_wrong_time = Column(DateTime, server_default=func.now())
    last_answer = Column(String(20))
    mastered = Column(SmallInteger, default=0)
    # 错题来源：practice=刷题，exam=在线考试/学员自测卷
    source = Column(String(10), default="practice", index=True)
    # 最近一次答错所属考试，便于错题本展示“来自哪场考试”
    exam_id = Column(BigInteger, index=True)


class QuestionMark(Base):
    """学员对单题的收藏、文字笔记与画重点标注（按用户 + 题目唯一）"""
    __tablename__ = "question_marks"
    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uq_question_mark"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    question_id = Column(BigInteger, nullable=False, index=True)
    is_favorite = Column(SmallInteger, default=0)
    note = Column(Text)
    annotation = Column(Text)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


