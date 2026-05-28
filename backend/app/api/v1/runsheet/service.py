from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai import compliance_validator, conflict_detector, notes_generator, scheduling_engine, scorer
from app.ai.pattern_analyser import analyse_patterns
from app.ai.recommendations.cultural_calendar import get_holiday_for_date
from app.ai.recommendations.mood_advisor import get_mood_advice
from app.ai.recommendations.library import LIBRARY
from app.ai.recommendations.station_profile import (
    StationProfile,
    all_window_labels,
    build_station_profile,
)
from app.api.v1.runsheet.models import RunSheetRecord
from app.api.v1.runsheet.schemas import (
    ComplianceViolation,
    Conflict,
    ProgrammeInput,
    Recommendation,
    RunSheetResponse,
    RunSheetStats,
    Segment,
    SegmentType,
    UpdateSegmentsRequest,
    UpdateSegmentsResponse,
)
from app.api.v1.user.statistics import load_user_statistics
from app.core.exceptions import NotFoundException
from app.models.audit_log import log_action


class RunSheetSummary(BaseModel):
    id: str
    station_name: str
    programme_type: str
    total_duration_minutes: int
    generated_at: str


# ---------------------------------------------------------------------------
# Score calculation (Session K2 — Part 4)
# ---------------------------------------------------------------------------

_SEVERITY_PENALTIES = {
    "critical":   20,
    "warning":    10,
    "suggestion": 5,
    "tip":        1,
}

_SEVERITY_ORDER = {"critical": 0, "warning": 1, "suggestion": 2, "tip": 3}


def _quality_score(recommendations: list[Recommendation]) -> float:
    """Quality score from recommendation severities — returned as 0.0-1.0."""
    raw = 100
    for r in recommendations:
        raw -= _SEVERITY_PENALTIES.get(r.severity, 0)
    raw = max(0, min(100, raw))
    return round(raw / 100, 4)


# ---------------------------------------------------------------------------
# generate_runsheet
# ---------------------------------------------------------------------------

async def generate_runsheet(
    payload: ProgrammeInput,
    db: Session,
    user_id: str | None = None,
) -> RunSheetResponse:
    segments: list[Segment] = scheduling_engine.generate(payload)
    segments = notes_generator.generate_notes(segments, payload)

    user_stats = load_user_statistics(db, str(user_id)) if user_id else {}
    user_settings = _load_user_settings(db, user_id)
    station_profile = build_station_profile(user_stats or None, user_settings)

    conflicts: list[Conflict] = conflict_detector.detect_conflicts(
        segments, payload, station_profile=station_profile
    )

    static_recs, _ = scorer.generate_recommendations(
        segments,
        payload,
        user_stats=user_stats if user_stats else None,
        deep_dive=payload.deep_dive,
        station_profile=station_profile,
        user_settings=user_settings,
    )

    runsheet_id  = str(uuid.uuid4())
    generated_at = datetime.now(timezone.utc).isoformat()
    comp = compliance_validator.validate_compliance(segments, payload)
    score = _quality_score(static_recs)
    stats = _compute_stats(segments, conflicts, score)

    # Run pattern analysis over the user's prior history (record not yet stored).
    pattern_recs: list[Recommendation] = []
    if user_id:
        provisional = RunSheetResponse(
            runsheet_id=runsheet_id,
            programme_input=payload,
            segments=segments,
            conflicts=conflicts,
            recommendations=static_recs,
            compliance_score=comp.compliance_score,
            compliance_risk=comp.compliance_risk,
            compliance_violations=comp.compliance_violations,
            stats=stats,
            generated_at=generated_at,
            deep_dive_insights=[],
        )
        pattern_recs = analyse_patterns(user_id, db, provisional)
        pattern_recs.sort(key=lambda r: (_SEVERITY_ORDER.get(r.severity, 99), -r.impact_score))

    recommendations: list[Recommendation] = list(static_recs) + pattern_recs

    deep_dive_insights = _build_deep_dive_insights(
        payload, recommendations, user_stats, station_profile
    ) if payload.deep_dive else []

    record = RunSheetRecord(
        id=runsheet_id,
        user_id=user_id,
        programme_type=payload.programme_type.value,
        station_name=payload.station_name,
        presenter_name=payload.presenter_name,
        total_duration_minutes=payload.total_duration_minutes,
        segments_json=json.dumps([s.model_dump(mode="json") for s in segments]),
        conflicts_json=json.dumps([c.model_dump(mode="json") for c in conflicts]),
        recommendations_json=json.dumps([r.model_dump(mode="json") for r in recommendations]),
        stats_json=json.dumps(stats.model_dump(mode="json")),
        programme_input_json=json.dumps(payload.model_dump(mode="json")),
        generated_at=generated_at,
    )
    db.add(record)
    db.commit()
    log_action(db, user_id, "runsheet_generated",
               f"station={payload.station_name}, id={runsheet_id}")

    return RunSheetResponse(
        runsheet_id=runsheet_id,
        programme_input=payload,
        segments=segments,
        conflicts=conflicts,
        recommendations=recommendations,
        compliance_score=comp.compliance_score,
        compliance_risk=comp.compliance_risk,
        compliance_violations=comp.compliance_violations,
        stats=stats,
        generated_at=generated_at,
        deep_dive_insights=deep_dive_insights,
    )


def _build_deep_dive_insights(
    payload: ProgrammeInput,
    recommendations: list[Recommendation],
    user_stats: dict,
    station_profile: StationProfile | None = None,
) -> list[str]:
    insights: list[str] = []

    holiday = get_holiday_for_date(payload.broadcast_date)
    if holiday:
        insights.append(f"Cultural calendar checked: {holiday} on this date.")
    else:
        insights.append("Cultural calendar checked: no holidays on this date.")

    try:
        advice = get_mood_advice(payload.start_time, payload.broadcast_date.weekday())
        genres = ", ".join(advice.get("preferred_genres", []))
        insights.append(
            f"Mood advisor: {payload.start_time} maps to "
            f"{advice.get('energy_level', 'unknown')}"
            + (f" — preferred genres: {genres}" if genres else "")
            + "."
        )
    except Exception:
        insights.append(f"Mood advisor: time-of-day analysis attempted for {payload.start_time}.")

    if station_profile and station_profile.has_any_data():
        parts: list[str] = []
        if station_profile.peak_windows:
            parts.append(
                f"{len(station_profile.peak_windows)} custom peak "
                f"{'window' if len(station_profile.peak_windows) == 1 else 'windows'} "
                f"({all_window_labels(station_profile.peak_windows)})"
            )
        if station_profile.audience_size_by_hour:
            parts.append(
                f"audience-size weighting active across "
                f"{len(station_profile.audience_size_by_hour)} hours"
            )
        if station_profile.low_windows:
            parts.append(
                f"{len(station_profile.low_windows)} low-listenership "
                f"{'window' if len(station_profile.low_windows) == 1 else 'windows'} respected"
            )
        if parts:
            insights.append("Station profile applied: " + ", ".join(parts) + ".")

        if station_profile.preferred_languages:
            langs = ", ".join(station_profile.preferred_languages)
            insights.append(
                f"Local language preference ({langs}) factored into "
                "content recommendations."
            )

        if station_profile.is_rural():
            insights.append(
                "Rural audience profile: agricultural and local-language "
                "content boosted."
            )
        elif station_profile.is_urban():
            insights.append(
                "Urban audience profile: traffic, commute and social-media "
                "engagement boosted."
            )

        if station_profile.local_notes:
            insights.append("User statistics applied: local cultural note surfaced.")
        if station_profile.custom_recommendations:
            insights.append("User statistics applied: custom recommendation included.")
    else:
        insights.append(
            "No station statistics found — using default Ghana audience "
            "models. Add station statistics for personalised analysis."
        )

    insights.append(f"All {len(LIBRARY)} recommendation rules evaluated.")

    return insights


def _load_user_settings(db: Session, user_id: str | None):
    if not user_id:
        return None
    from app.models.user import User
    return db.query(User).filter(User.id == user_id).first()


# ---------------------------------------------------------------------------
# get_history
# ---------------------------------------------------------------------------

async def get_history(
    db: Session,
    user_id: str | None = None,
) -> list[RunSheetSummary]:
    q = db.query(RunSheetRecord)
    if user_id:
        q = q.filter(RunSheetRecord.user_id == user_id)
    records = q.order_by(RunSheetRecord.generated_at.desc()).limit(20).all()
    return [
        RunSheetSummary(
            id=r.id,
            station_name=r.station_name,
            programme_type=r.programme_type,
            total_duration_minutes=r.total_duration_minutes,
            generated_at=r.generated_at,
        )
        for r in records
    ]


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------

async def get_by_id(
    runsheet_id: str,
    db: Session,
    user_id: str | None = None,
) -> RunSheetResponse:
    q = db.query(RunSheetRecord).filter(RunSheetRecord.id == runsheet_id)
    if user_id:
        q = q.filter(RunSheetRecord.user_id == user_id)
    record = q.first()
    if not record:
        raise NotFoundException(f"Run-sheet '{runsheet_id}' not found")
    return _record_to_response(record)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _record_to_response(record: RunSheetRecord) -> RunSheetResponse:
    segments = [Segment(**s) for s in json.loads(record.segments_json)]
    conflicts = [Conflict(**c) for c in json.loads(record.conflicts_json)]
    recommendations = [Recommendation(**r) for r in json.loads(record.recommendations_json)]
    stats = RunSheetStats(**json.loads(record.stats_json))
    programme_input = ProgrammeInput(**json.loads(record.programme_input_json))
    comp = compliance_validator.validate_compliance(segments, programme_input)

    return RunSheetResponse(
        runsheet_id=record.id,
        programme_input=programme_input,
        segments=segments,
        conflicts=conflicts,
        recommendations=recommendations,
        compliance_score=comp.compliance_score,
        compliance_risk=comp.compliance_risk,
        compliance_violations=comp.compliance_violations,
        stats=stats,
        generated_at=record.generated_at,
        deep_dive_insights=[],
    )


# ---------------------------------------------------------------------------
# update_segments
# ---------------------------------------------------------------------------

async def update_segments(
    payload: UpdateSegmentsRequest,
    db: Session,
    user_id: str | None = None,
) -> UpdateSegmentsResponse:
    q = db.query(RunSheetRecord).filter(RunSheetRecord.id == payload.runsheet_id)
    if user_id:
        q = q.filter(RunSheetRecord.user_id == user_id)
    record = q.first()
    if not record:
        raise NotFoundException(f"Run-sheet '{payload.runsheet_id}' not found")

    programme_input = ProgrammeInput(**json.loads(record.programme_input_json))

    segments = _recalc_times(payload.segments)

    user_stats = load_user_statistics(db, str(user_id)) if user_id else {}
    user_settings = _load_user_settings(db, user_id)
    station_profile = build_station_profile(user_stats or None, user_settings)

    conflicts: list[Conflict] = conflict_detector.detect_conflicts(
        segments, programme_input, station_profile=station_profile
    )

    recommendations, _ = scorer.generate_recommendations(
        segments,
        programme_input,
        user_stats=user_stats if user_stats else None,
        deep_dive=programme_input.deep_dive,
        station_profile=station_profile,
        user_settings=user_settings,
    )
    score = _quality_score(recommendations)
    stats = _compute_stats(segments, conflicts, score)
    comp = compliance_validator.validate_compliance(segments, programme_input)

    record.segments_json = json.dumps([s.model_dump(mode="json") for s in segments])
    record.conflicts_json = json.dumps([c.model_dump(mode="json") for c in conflicts])
    record.recommendations_json = json.dumps([r.model_dump(mode="json") for r in recommendations])
    record.stats_json = json.dumps(stats.model_dump(mode="json"))
    db.commit()
    log_action(db, user_id, "segments_updated", f"runsheet_id={payload.runsheet_id}")

    return UpdateSegmentsResponse(
        segments=segments,
        conflicts=conflicts,
        stats=stats,
        compliance_score=comp.compliance_score,
        compliance_risk=comp.compliance_risk,
        compliance_violations=comp.compliance_violations,
    )


# ---------------------------------------------------------------------------
# Time helpers (mirrors conflict_detector without importing private symbols)
# ---------------------------------------------------------------------------

def _hhmm_to_minutes(t: str) -> int:
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def _minutes_to_hhmm(minutes: int) -> str:
    minutes = minutes % (24 * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _recalc_times(segments: list[Segment]) -> list[Segment]:
    if not segments:
        return []
    result: list[Segment] = []
    cursor = _hhmm_to_minutes(segments[0].start_time)
    for seg in segments:
        new_start = _minutes_to_hhmm(cursor)
        new_end = _minutes_to_hhmm(cursor + seg.duration_minutes)
        result.append(seg.model_copy(update={"start_time": new_start, "end_time": new_end}))
        cursor += seg.duration_minutes
    return result


def _compute_stats(
    segments: list[Segment],
    conflicts: list[Conflict],
    score: float,
) -> RunSheetStats:
    total_dur = sum(s.duration_minutes for s in segments)
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
