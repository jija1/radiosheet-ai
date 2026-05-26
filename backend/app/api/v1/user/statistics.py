from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.user.schemas import UserStatisticEntry, UserStatisticUpsert
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.user_statistics import UserStatistic

router = APIRouter()


@router.get("/statistics", response_model=list[UserStatisticEntry])
async def list_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[UserStatisticEntry]:
    records = (
        db.query(UserStatistic)
        .filter(UserStatistic.user_id == current_user.id)
        .order_by(UserStatistic.stat_key.asc())
        .all()
    )
    return [
        UserStatisticEntry(
            stat_key=r.stat_key,
            stat_value=r.stat_value,
            notes=r.notes,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in records
    ]


@router.post("/statistics", response_model=UserStatisticEntry)
async def upsert_statistic(
    payload: UserStatisticUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserStatisticEntry:
    key = payload.stat_key.strip()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="stat_key cannot be empty",
        )
    now = datetime.now(timezone.utc).isoformat()
    existing = (
        db.query(UserStatistic)
        .filter(UserStatistic.user_id == current_user.id, UserStatistic.stat_key == key)
        .first()
    )
    if existing:
        existing.stat_value = payload.stat_value
        existing.notes = payload.notes
        existing.updated_at = now
    else:
        existing = UserStatistic(
            user_id=current_user.id,
            stat_key=key,
            stat_value=payload.stat_value,
            notes=payload.notes,
            created_at=now,
            updated_at=now,
        )
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return UserStatisticEntry(
        stat_key=existing.stat_key,
        stat_value=existing.stat_value,
        notes=existing.notes,
        created_at=existing.created_at,
        updated_at=existing.updated_at,
    )


@router.delete("/statistics/{stat_key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_statistic(
    stat_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    existing = (
        db.query(UserStatistic)
        .filter(UserStatistic.user_id == current_user.id, UserStatistic.stat_key == stat_key)
        .first()
    )
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Statistic '{stat_key}' not found",
        )
    db.delete(existing)
    db.commit()


def load_user_statistics(db: Session, user_id: str) -> dict[str, UserStatistic]:
    """Return all user statistics keyed by stat_key. Used by recommendations engine."""
    records = (
        db.query(UserStatistic)
        .filter(UserStatistic.user_id == user_id)
        .all()
    )
    return {r.stat_key: r for r in records}
