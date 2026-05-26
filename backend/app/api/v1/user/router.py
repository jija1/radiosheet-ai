from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.v1.runsheet.models import RunSheetRecord
from app.api.v1.runsheet.schemas import ProgrammeInput, Segment, SegmentType
from app.api.v1.user.schemas import (
    AccountDeleteRequest,
    AuditLogEntry,
    DashboardResponse,
    PatternsResponse,
    ProfileResponse,
    ProfileStats,
    ProfileUpdateRequest,
    RunSheetRecordSummary,
    ScoreTrendPoint,
    UserInfo,
    UserSettings,
    UserSettingsUpdate,
    UsualSetup,
)
from app.api.v1.user.statistics import router as statistics_router
from app.dependencies import get_current_user, get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.user_statistics import UserStatistic

router = APIRouter()
router.include_router(statistics_router)


@router.get("/me", response_model=UserInfo)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserInfo:
    return UserInfo(
        email=current_user.email,
        created_at=current_user.created_at or "",
    )


def _purge_old_audit_logs(db: Session, user_id: str, retention_days: int) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    cutoff_iso = cutoff.isoformat()
    db.query(AuditLog).filter(
        AuditLog.user_id == str(user_id),
        AuditLog.created_at < cutoff_iso,
    ).delete(synchronize_session=False)
    db.commit()


@router.get("/audit-log", response_model=list[AuditLogEntry])
async def get_audit_log(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AuditLogEntry]:
    retention = current_user.audit_log_retention_days or 90
    _purge_old_audit_logs(db, str(current_user.id), retention)

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

    avg_score = round(sum(scores) / len(scores), 3) if scores else 0.0

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
        analytics_opted_out=bool(user.analytics_opted_out) if user.analytics_opted_out is not None else False,
        audit_log_retention_days=user.audit_log_retention_days or 90,
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

    average_score = round(sum(scores) / len(scores), 3) if scores else 0.0

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


_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _hhmm_to_minutes(t: str) -> int:
    h, m = t.split(":")
    return int(h) * 60 + int(m)


@router.get("/patterns", response_model=PatternsResponse)
async def get_patterns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PatternsResponse:
    records = (
        db.query(RunSheetRecord)
        .filter(RunSheetRecord.user_id == current_user.id)
        .order_by(RunSheetRecord.generated_at.desc())
        .all()
    )

    if not records:
        return PatternsResponse(runsheet_count=0)

    score_trend: list[ScoreTrendPoint] = []
    news_offsets: list[int] = []
    advert_offsets: list[int] = []
    talk_durations: list[int] = []
    programme_types: list[str] = []
    durations: list[int] = []
    presenters: list[str] = []
    stations: list[str] = []
    prefs: list[str] = []
    day_scores: dict[int, list[float]] = {}

    for r in records[:20][::-1]:
        stats = json.loads(r.stats_json)
        prog_data = json.loads(r.programme_input_json)
        score = float(stats.get("score", 0.0))
        date_str = str(prog_data.get("broadcast_date", "")) or r.generated_at[:10]
        score_trend.append(ScoreTrendPoint(date=date_str, score=score))

    for r in records:
        stats = json.loads(r.stats_json)
        prog_data = json.loads(r.programme_input_json)
        prog = ProgrammeInput(**prog_data)
        segments = [Segment(**s) for s in json.loads(r.segments_json)]
        prog_start = _hhmm_to_minutes(prog.start_time)

        programme_types.append(r.programme_type)
        durations.append(r.total_duration_minutes)
        presenters.append(r.presenter_name)
        stations.append(r.station_name)
        prefs.append(prog.talk_music_preference.value)

        news = next((s for s in segments if s.type == SegmentType.NEWS), None)
        if news:
            news_offsets.append(_hhmm_to_minutes(news.start_time) - prog_start)

        ad = next((s for s in segments if s.type == SegmentType.ADVERT), None)
        if ad:
            advert_offsets.append(_hhmm_to_minutes(ad.start_time) - prog_start)

        for s in segments:
            if s.type in {SegmentType.TALK, SegmentType.INTERVIEW}:
                talk_durations.append(s.duration_minutes)

        day = prog.broadcast_date.weekday()
        day_scores.setdefault(day, []).append(float(stats.get("score", 0.0)))

    most_used_type = Counter(programme_types).most_common(1)[0][0] if programme_types else None

    typical_news = (sum(news_offsets) / len(news_offsets)) if news_offsets else None
    typical_advert = (sum(advert_offsets) / len(advert_offsets)) if advert_offsets else None
    avg_talk = (sum(talk_durations) / len(talk_durations)) if talk_durations else None

    best_day: str | None = None
    if day_scores:
        best_idx = max(day_scores.items(), key=lambda kv: sum(kv[1]) / len(kv[1]))[0]
        best_day = _DAY_NAMES[best_idx]

    usual_setup: UsualSetup | None = None
    if records:
        usual_setup = UsualSetup(
            station_name=Counter(stations).most_common(1)[0][0] if stations else None,
            presenter_name=Counter(presenters).most_common(1)[0][0] if presenters else None,
            programme_type=most_used_type,
            duration_minutes=Counter(durations).most_common(1)[0][0] if durations else None,
            talk_music_preference=Counter(prefs).most_common(1)[0][0] if prefs else None,
        )

    return PatternsResponse(
        runsheet_count=len(records),
        score_trend=score_trend,
        most_used_programme_type=most_used_type,
        typical_news_placement_minute=typical_news,
        typical_first_advert_minute=typical_advert,
        average_talk_duration=avg_talk,
        best_performing_day=best_day,
        usual_setup=usual_setup,
    )


@router.get("/export")
async def export_user_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    profile = _build_profile(db, current_user)
    settings_data = _user_to_settings(current_user)

    statistics = (
        db.query(UserStatistic)
        .filter(UserStatistic.user_id == current_user.id)
        .all()
    )
    stats_data = [
        {
            "stat_key": s.stat_key,
            "stat_value": s.stat_value,
            "notes": s.notes,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }
        for s in statistics
    ]

    runsheets = (
        db.query(RunSheetRecord)
        .filter(RunSheetRecord.user_id == current_user.id)
        .order_by(RunSheetRecord.generated_at.desc())
        .all()
    )
    runsheet_summaries = []
    for r in runsheets:
        stats = json.loads(r.stats_json)
        prog_input = json.loads(r.programme_input_json)
        runsheet_summaries.append({
            "runsheet_id": r.id,
            "programme_type": r.programme_type,
            "station_name": r.station_name,
            "presenter_name": r.presenter_name,
            "broadcast_date": str(prog_input.get("broadcast_date", "")),
            "total_duration_minutes": r.total_duration_minutes,
            "generated_at": r.generated_at,
            "conflict_count": int(stats.get("conflict_count", 0)),
            "score": float(stats.get("score", 0.0)),
        })

    audit_logs = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == str(current_user.id))
        .order_by(AuditLog.created_at.desc())
        .all()
    )
    audit_data = [
        {"action": a.action, "detail": a.detail, "created_at": a.created_at}
        for a in audit_logs
    ]

    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile.model_dump(),
        "settings": settings_data.model_dump(),
        "statistics": stats_data,
        "runsheets": runsheet_summaries,
        "audit_log": audit_data,
    }
    body = json.dumps(payload, indent=2, default=str)
    return Response(
        content=body,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="radiosheet_data.json"'},
    )


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    payload: AccountDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    if not bcrypt.checkpw(payload.password.encode("utf-8"),
                          current_user.hashed_password.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )

    user_id = current_user.id
    db.query(UserStatistic).filter(UserStatistic.user_id == user_id).delete(synchronize_session=False)
    db.query(RunSheetRecord).filter(RunSheetRecord.user_id == user_id).delete(synchronize_session=False)
    db.query(AuditLog).filter(AuditLog.user_id == str(user_id)).delete(synchronize_session=False)
    db.delete(current_user)
    db.commit()
