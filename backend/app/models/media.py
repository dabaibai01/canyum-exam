from sqlalchemy import Column, BigInteger, Integer, String, Text, Integer, SmallInteger, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category_id = Column(BigInteger, index=True)
    video_url = Column(String(500), nullable=False)
    cover_image = Column(String(255))
    duration = Column(Integer)
    sort = Column(Integer, default=0)
    status = Column(SmallInteger, default=1)
    created_at = Column(DateTime, server_default=func.now())

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    author = Column(String(100))
    description = Column(Text)
    category_id = Column(BigInteger, index=True)
    cover_image = Column(String(255))
    file_url = Column(String(500))
    sort = Column(Integer, default=0)
    status = Column(SmallInteger, default=1)
    created_at = Column(DateTime, server_default=func.now())


