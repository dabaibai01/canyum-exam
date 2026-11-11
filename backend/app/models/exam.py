from sqlalchemy import Column, BigInteger, Integer, String, Text, Integer, SmallInteger, DateTime, Numeric
from sqlalchemy.sql import func
from app.core.database import Base

class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category_id = Column(BigInteger, index=True)
    total_score = Column(Numeric(5, 1), default=100.0)
    duration = Column(Integer)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    question_count = Column(Integer, default=0)
    pass_score = Column(Numeric(5, 1), default=60.0)
    status = Column(SmallInteger, default=0, index=True)
    # 重考设置：allow_retake 是否允许重考；retake_limit 可重考次数（0 表示不限）
    allow_retake = Column(SmallInteger, default=0)
    retake_limit = Column(Integer, default=0)
    created_by = Column(BigInteger)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class ExamQuestion(Base):
    __tablename__ = "exam_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(BigInteger, nullable=False, index=True)
    question_id = Column(BigInteger, nullable=False)
    score = Column(Numeric(5, 1), default=1.0)
    sort = Column(Integer, default=0)

class ExamAttempt(Base):
    """一次交卷记录，用于成绩查询与重考次数限制"""
    __tablename__ = "exam_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    score = Column(Numeric(6, 1), default=0)
    total_score = Column(Numeric(6, 1), default=0)
    correct_count = Column(Integer, default=0)
    question_count = Column(Integer, default=0)
    answered_count = Column(Integer, default=0)
    passed = Column(SmallInteger, default=0)
    submitted_at = Column(DateTime, server_default=func.now())


