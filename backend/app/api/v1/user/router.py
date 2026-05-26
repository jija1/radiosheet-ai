from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.runsheet.models import RunSheetRecord
from app.api.v1.user.schemas import (
    AuditLogEntry,
    DashboardResponse,
    ProfileResponse,
    ProfileStats,
    ProfileUpdateRequest,
    RunSheetRecordSummary,
    UserInfo,
    UserSettings,
    UserSettingsUpdate,
)
from app.dependencies import get_current_user, get_db
from app.models.audit_log import AuditLog
from app.models.user import User

router = APIRouter()


@router.get("/me", response_model=UserInfo)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserInfo:
    return UserInfo(
        email=current_user.email,
        created_at=current_user.created_at or "",
    )


@router.get("/audit-log", response_model=list[AuditLogEntry])
async def get_audit_log(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AuditLogEntry]:
    records = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == str(current_user.id))
        .order_by(AuditLog.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        AuditLogEntry(action=r.action, detail=r.detail, created_at=r.created_at)
        for r in records
    ]


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    return _build_profile(db, current_user)


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    cleaned = payload.display_name.strip()
    current_user.display_name = cleaned if cleaned else None
    db.commit()
    return _build_profile(db, current_user)


def _build_profile(db: Session, user: User) -> ProfileResponse:
    records = (
        db.query(RunSheetRecord)
        .filter(RunSheetRecord.user_id == user.id)
        .all()
    )
    scores: list[float] = []
    total_conflicts = 0
    for r in records:
        stats = json.loads(r.stats_json)
        scores.append(float(stats.get("score", 0.0)))
        total_conflicts += int(stats.get("conflict_count", 0))

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    return ProfileResponse(
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at or "",
        last_login=user.last_login,
        stats=ProfileStats(
            total_runsheets=len(records),
            average_score=avg_score,
            total_conflicts_resolved=total_conflicts,
        ),
    )


@router.get("/settings", response_model=UserSettings)
async def get_settings(
    current_user: User = Depends(get_current_user),
) -> UserSettings:
    return _user_to_settings(current_user)


@router.patch("/settings", response_model=UserSettings)
async def update_settings(
    payload: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserSettings:
    update = payload.model_dump(exclude_none=True)
    for field, value in update.items():
        setattr(current_user, field, value)
    db.commit()
    return _user_to_settings(current_user)


def _user_to_settings(user: User) -> UserSettings:
    return UserSettings(
        default_station_name=user.default_station_name,
        default_presenter_name=user.default_presenter_name,
        default_programme_type=user.default_programme_type,
        default_duration_minutes=user.default_duration_minutes,
        default_talk_music_preference=user.default_talk_music_preference,
        default_max_adverts_per_hour=user.default_max_adverts_per_hour,
        time_format=user.time_format or "24h",
        cultural_calendar_enabled=user.cultural_calendar_enabled if user.cultural_calendar_enabled is not None else True,
        strict_mode=user.strict_mode if user.strict_mode is not None else False,
        auto_apply_fixes=user.auto_apply_fixes if user.auto_apply_fixes is not None else False,
        notifications_enabled=user.notifications_enabled if user.notifications_enabled is not None else True,
        default_region=user.default_region,
        station_audience=user.station_audience,
        recommendation_depth=user.recommendation_depth or "standard",
    )


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    records = (
        db.query(RunSheetRecord)
        .filter(RunSheetRecord.user_id == current_user.id)
        .order_by(RunSheetRecord.generated_at.desc())
        .all()
    )

    total_runsheets = len(records)
    scores: list[float] = []
    total_conflicts_resolved = 0

    for r in records:
        stats = json.loads(r.stats_json)
        scores.append(float(stats.get("score", 0.0)))
        total_conflicts_resolved += int(stats.get("conflict_count", 0))

    average_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    recent_summaries: list[RunSheetRecordSummary] = []
    for r in records[:5]:
        stats = json.loads(r.stats_json)
        prog_input = json.loads(r.programme_input_json)
        recent_summaries.append(
            RunSheetRecordSummary(
                runsheet_id=r.id,
                programme_type=r.programme_type,
                station_name=r.station_name,
                broadcast_date=str(prog_input.get("broadcast_date", "")),
                generated_at=r.generated_at,
                conflict_count=int(stats.get("conflict_count", 0)),
                score=float(stats.get("score", 0.0)),
            )
        )

    return DashboardResponse(
        total_runsheets=total_runsheets,
        recent_runsheets=recent_summaries,
        average_score=average_score,
        total_conflicts_resolved=total_conflicts_resolved,
    )
