from sqlalchemy import Column, BigInteger, Integer, String, Text, Integer, SmallInteger, DateTime, Numeric
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


