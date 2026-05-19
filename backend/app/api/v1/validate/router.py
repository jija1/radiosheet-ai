from __future__ import annotations

from fastapi import APIRouter, Depends

from app.ai import compliance_validator, conflict_detector, scorer
from app.api.v1.runsheet.schemas import (
    Conflict,
    Recommendation,
    RunSheetStats,
    Segment,
    SegmentType,
)
from app.api.v1.validate.schemas import ValidateRequest, ValidateResponse
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/runsheet", response_model=ValidateResponse)
async def validate_runsheet(
    payload: ValidateRequest,
    current_user: User = Depends(get_current_user),
) -> ValidateResponse:
    segments = payload.segments
    programme_input = payload.programme_input

    conflicts: list[Conflict] = conflict_detector.detect_conflicts(segments, programme_input)
    comp = compliance_validator.validate_compliance(segments, programme_input)
    recommendations: list[Recommendation]
    recommendations, score = scorer.generate_recommendations(segments, programme_input)
    stats = _compute_stats(segments, conflicts, score)

    return ValidateResponse(
        segments=segments,
        conflicts=conflicts,
        compliance_score=comp.compliance_score,
        compliance_risk=comp.compliance_risk,
        compliance_violations=comp.compliance_violations,
        stats=stats,
        recommendations=recommendations,
    )


def _compute_stats(
    segments: list[Segment],
    conflicts: list[Conflict],
    score: float,
) -> RunSheetStats:
    total_dur   = sum(s.duration_minutes for s in segments)
    music_mins  = sum(s.duration_minutes for s in segments if s.type == SegmentType.MUSIC)
    talk_mins   = sum(s.duration_minutes for s in segments if s.type == SegmentType.TALK)
    advert_mins = sum(s.duration_minutes for s in segments if s.type == SegmentType.ADVERT)

    if total_dur > 0:
        music_pct  = round(music_mins  / total_dur * 100, 1)
        talk_pct   = round(talk_mins   / total_dur * 100, 1)
        advert_pct = round(advert_mins / total_dur * 100, 1)
    else:
        music_pct = talk_pct = advert_pct = 0.0

    return RunSheetStats(
        total_segments=len(segments),
        total_duration_minutes=total_dur,
        music_percentage=music_pct,
        talk_percentage=talk_pct,
        advert_percentage=advert_pct,
        conflict_count=len(conflicts),
        score=score,
    )
