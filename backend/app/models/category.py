from sqlalchemy import Column, BigInteger, Integer, String, Integer, SmallInteger, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(BigInteger, default=0, index=True)
    type = Column(String(20), default="question", index=True)
    sort = Column(Integer, default=0)
    status = Column(SmallInteger, default=1)
    created_at = Column(DateTime, server_default=func.now())


