from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String

from app.db.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id         = Column(String, primary_key=True)
    user_id    = Column(String, nullable=False, index=True)
    action     = Column(String, nullable=False)
    detail     = Column(String, nullable=False, default="")
    created_at = Column(String, nullable=False)


def log_action(db, user_id: str | None, action: str, detail: str = "") -> None:
    """Fire-and-forget audit logger. Never raises."""
    if not user_id:
        return
    try:
        entry = AuditLog(
            id=str(uuid.uuid4()),
            user_id=str(user_id),
            action=action,
            detail=detail,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        db.add(entry)
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
