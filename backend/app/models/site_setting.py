from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class SiteSetting(Base):
    """站点可配置项，按 key/value 存储，便于后续扩展。"""

    __tablename__ = "site_settings"

    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=False, default="")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
