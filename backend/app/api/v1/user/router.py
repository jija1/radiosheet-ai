from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.runsheet.models import RunSheetRecord
from app.api.v1.user.schemas import AuditLogEntry, DashboardResponse, RunSheetRecordSummary, UserInfo
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
