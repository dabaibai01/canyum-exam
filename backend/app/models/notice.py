from sqlalchemy import Column, Integer, String, Text, SmallInteger, DateTime, BigInteger
from sqlalchemy.sql import func
from app.core.database import Base


class Notice(Base):
    """系统公告：后台可新建、编辑、发布/下线，学员端首页展示已发布的公告"""
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(120), nullable=False)
    content = Column(Text, nullable=False)
    # 0 草稿（不展示） 1 已发布（学员端可见）
    status = Column(SmallInteger, default=0, index=True)
    created_by = Column(BigInteger)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
