from sqlalchemy import Column, BigInteger, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    real_name = Column(String(50), nullable=False)
    phone = Column(String(20), index=True)
    role = Column(String(20), default="user")
    status = Column(
        String(20),
        nullable=False,
        default="approved",
        server_default="approved",
        index=True,
        comment="pending=待审核, approved=已通过, rejected=已拒绝",
    )
    department = Column(String(100))
    position = Column(String(100))
    avatar = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


