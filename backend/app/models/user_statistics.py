from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, String, Text

from app.db.session import Base


class UserStatistic(Base):
    __tablename__ = "user_statistics"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(String,  ForeignKey("users.id"), nullable=False, index=True)
    stat_key   = Column(String(100), nullable=False, index=True)
    stat_value = Column(Text,    nullable=False, default="")
    notes      = Column(Text,    nullable=True)
    created_at = Column(String,  nullable=False)
    updated_at = Column(String,  nullable=False)
