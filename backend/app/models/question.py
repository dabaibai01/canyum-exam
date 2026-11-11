from sqlalchemy import Column, BigInteger, Integer, String, Text, Integer, SmallInteger, DateTime, Numeric
from sqlalchemy.sql import func
from app.core.database import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(BigInteger, nullable=False, index=True)
    type = Column(String(20), nullable=False, index=True)
    content = Column(Text, nullable=False)
    image = Column(String(255))
    analysis = Column(Text)
    difficulty = Column(SmallInteger, default=1)
    score = Column(Numeric(5, 1), default=1.0)
    status = Column(SmallInteger, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class QuestionOption(Base):
    __tablename__ = "question_options"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(BigInteger, nullable=False, index=True)
    label = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    is_correct = Column(SmallInteger, default=0)
    sort = Column(Integer, default=0)


