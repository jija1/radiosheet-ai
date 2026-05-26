"""
Pattern analyser — surfaces personalised, history-based recommendations.

Pure statistical analysis of a user's stored run-sheets. No ML, no LLM.
Requires at least 5 past run-sheets before any check can fire (P008
included). All returned Recommendations have based_on_history=True.

The signature in the spec uses `user_id: int`, but the project stores
users by UUID string — we accept either and coerce to str for the query.
"""
from __future__ import annotations

import json
from collections import Counter
from statistics import mean
from typing import Any

from sqlalchemy.orm import Session

from app.api.v1.runsheet.models import RunSheetRecord
from app.api.v1.runsheet.schemas import (
    ProgrammeInput,
    Recommendation,
    RunSheetResponse,
    Segment,
    SegmentType,
)
from app.models.user import User

_SOURCE = "Your run-sheet history (RadioSheet AI pattern analysis)"


def analyse_patterns(
    user_id: Any,
    db: Session,
    current_runsheet: RunSheetResponse,
) -> list[Recommendation]:
    """Return pattern-based recommendations sourced from the user's history."""
    if user_id is None:
        return []

    uid = str(user_id)
    records: list[RunSheetRecord] = (
        db.query(RunSheetRecord)
        .filter(RunSheetRecord.user_id == uid)
        .order_by(RunSheetRecord.generated_at.desc())
        .all()
    )

    if len(records) < 5:
        return []

    confidence = "high" if len(records) >= 10 else "medium"
    history = [_decode_record(r) for r in records]
    user = db.query(User).filter(User.id == uid).first()

    recs: list[Recommendation] = []
    recs.extend(_p001(history, current_runsheet, confidence))
    recs.extend(_p002(history, current_runsheet, confidence))
    recs.extend(_p003(history, current_runsheet, confidence))
    recs.extend(_p004(history, current_runsheet, confidence))
    recs.extend(_p005(history, current_runsheet, confidence))
    recs.extend(_p006(history, current_runsheet, confidence))
    recs.extend(_p007(history, current_runsheet, confidence))
    recs.extend(_p008(history, current_runsheet, user, confidence))
    return recs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hhmm_to_minutes(t: str) -> int:
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def _decode_record(record: RunSheetRecord) -> dict:
    segments = [Segment(**s) for s in json.loads(record.segments_json)]
    prog = ProgrammeInput(**json.loads(record.programme_input_json))
    stats = json.loads(record.stats_json)
    return {
        "id": record.id,
        "generated_at": record.generated_at,
        "programme_type": record.programme_type,
        "station_name": record.station_name,
        "presenter_name": record.presenter_name,
        "total_duration_minutes": record.total_duration_minutes,
        "broadcast_date": prog.broadcast_date,
        "start_time": prog.start_time,
        "programme_input": prog,
        "segments": segments,
        "score": float(stats.get("score", 0.0)),
    }


def _first_segment_of_type(
    segments: list[Segment], seg_type: SegmentType
) -> Segment | None:
    for s in segments:
        if s.type == seg_type:
            return s
    return None


def _minutes_from_start(seg: Segment, prog_start: str) -> int:
    return _hhmm_to_minutes(seg.start_time) - _hhmm_to_minutes(prog_start)


def _rec(
    rec_id: str,
    category: str,
    message: str,
    severity: str,
    impact: float,
    confidence: str,
) -> Recommendation:
    return Recommendation(
        recommendation_id=rec_id,
        category=category,
        message=message,
        impact_score=impact,
        source=_SOURCE,
        confidence=confidence,
        severity=severity,
        based_on_history=True,
    )


def _format_minutes(value: float) -> str:
    return f"{value:.0f}"


def _format_clock(prog_start: str, minute_offset: float) -> str:
    base = _hhmm_to_minutes(prog_start)
    total = int(round(base + minute_offset)) % (24 * 60)
    return f"{total // 60:02d}:{total % 60:02d}"


_DAY_NAMES = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]


# ---------------------------------------------------------------------------
# P001 — News placement consistency
# ---------------------------------------------------------------------------

def _p001(
    history: list[dict],
    current: RunSheetResponse,
    confidence: str,
) -> list[Recommendation]:
    offsets = []
    for h in history:
        seg = _first_segment_of_type(h["segments"], SegmentType.NEWS)
        if seg:
            offsets.append(_minutes_from_start(seg, h["start_time"]))
    if len(offsets) < 3:
        return []

    typical = mean(offsets)
    current_news = _first_segment_of_type(current.segments, SegmentType.NEWS)
    if not current_news:
        return []

    current_offset = _minutes_from_start(current_news, current.programme_input.start_time)
    if abs(current_offset - typical) <= 10:
        return []

    typical_clock = _format_clock(current.programme_input.start_time, typical)
    current_clock = current_news.start_time
    return [_rec(
        "P001", "pacing",
        f"Your news segment usually starts around {typical_clock}. "
        f"Today it's at {current_clock} — listeners may expect it earlier.",
        severity="suggestion",
        impact=0.55,
        confidence=confidence,
    )]


# ---------------------------------------------------------------------------
# P002 — First advert timing
# ---------------------------------------------------------------------------

def _p002(
    history: list[dict],
    current: RunSheetResponse,
    confidence: str,
) -> list[Recommendation]:
    offsets = []
    for h in history:
        seg = _first_segment_of_type(h["segments"], SegmentType.ADVERT)
        if seg:
            offsets.append(_minutes_from_start(seg, h["start_time"]))
    if len(offsets) < 3:
        return []

    typical = mean(offsets)
    current_ad = _first_segment_of_type(current.segments, SegmentType.ADVERT)
    if not current_ad:
        return []
    current_offset = _minutes_from_start(current_ad, current.programme_input.start_time)

    # Fire only when current is meaningfully *earlier* than typical
    if typical - current_offset < 8:
        return []

    return [_rec(
        "P002", "monetisation",
        f"You typically place your first advert at minute {_format_minutes(typical)}. "
        f"Today's placement at minute {_format_minutes(float(current_offset))} is earlier than "
        "your usual style — consider listener warm-up time.",
        severity="suggestion",
        impact=0.55,
        confidence=confidence,
    )]


# ---------------------------------------------------------------------------
# P003 — Interview / talk duration
# ---------------------------------------------------------------------------

def _p003(
    history: list[dict],
    current: RunSheetResponse,
    confidence: str,
) -> list[Recommendation]:
    talk_types = {SegmentType.TALK, SegmentType.INTERVIEW}
    historical_durations = [
        s.duration_minutes
        for h in history
        for s in h["segments"]
        if s.type in talk_types
    ]
    if len(historical_durations) < 3:
        return []
    avg = mean(historical_durations)
    if avg <= 0:
        return []

    longest_current = None
    for s in current.segments:
        if s.type in talk_types and s.duration_minutes >= avg * 2:
            if longest_current is None or s.duration_minutes > longest_current.duration_minutes:
                longest_current = s
    if longest_current is None:
        return []

    return [_rec(
        "P003", "pacing",
        f"Your talk segments average {_format_minutes(avg)} minutes across your "
        f"last {len(history)} run-sheets. Today's {longest_current.duration_minutes}-minute "
        "segment is significantly longer — consider breaking it up.",
        severity="warning",
        impact=0.70,
        confidence=confidence,
    )]


# ---------------------------------------------------------------------------
# P004 — Score trend
# ---------------------------------------------------------------------------

def _p004(
    history: list[dict],
    current: RunSheetResponse,
    confidence: str,
) -> list[Recommendation]:
    if len(history) < 5:
        return []
    overall_window = history[:20]
    recent_window = history[:5]
    overall_avg = mean(h["score"] for h in overall_window)
    recent_avg = mean(h["score"] for h in recent_window)

    # scores are 0.0-1.0; 15 "points" of the 0–100 display = 0.15
    if overall_avg - recent_avg < 0.15:
        return []

    return [_rec(
        "P004", "pacing",
        f"Your run-sheet quality score has been trending down recently "
        f"(recent average: {int(round(recent_avg * 100))}%, overall average: "
        f"{int(round(overall_avg * 100))}%). Review your last few run-sheets to "
        "identify patterns.",
        severity="warning",
        impact=0.75,
        confidence=confidence,
    )]


# ---------------------------------------------------------------------------
# P005 — High-scoring pattern match
# ---------------------------------------------------------------------------

def _p005(
    history: list[dict],
    current: RunSheetResponse,
    confidence: str,
) -> list[Recommendation]:
    top = [h for h in history if h["score"] >= 0.85]
    if len(top) < 3:
        return []

    presence: Counter = Counter()
    for h in top:
        types_in_runsheet = {s.type for s in h["segments"]}
        for t in types_in_runsheet:
            presence[t] += 1

    current_types = {s.type for s in current.segments}
    for seg_type, count in presence.items():
        share = count / len(top)
        if share >= 0.9 and seg_type not in current_types:
            return [_rec(
                "P005", "pacing",
                f"Your highest-scoring run-sheets (85%+) almost always include a "
                f"{seg_type.value.replace('_', ' ')} segment. Today's run-sheet "
                "doesn't have one.",
                severity="suggestion",
                impact=0.60,
                confidence=confidence,
            )]
    return []


# ---------------------------------------------------------------------------
# P006 — Day-of-week consistency
# ---------------------------------------------------------------------------

def _p006(
    history: list[dict],
    current: RunSheetResponse,
    confidence: str,
) -> list[Recommendation]:
    target_day = current.programme_input.broadcast_date.weekday()
    same_day_records = [h for h in history if h["broadcast_date"].weekday() == target_day]
    if len(same_day_records) < 3:
        return []

    openers = Counter()
    for h in same_day_records:
        if h["segments"]:
            openers[h["segments"][0].type] += 1

    if not openers:
        return []
    typical_opener, top_count = openers.most_common(1)[0]
    if top_count / len(same_day_records) < 0.5:
        return []

    if not current.segments:
        return []
    current_opener = current.segments[0].type
    if current_opener == typical_opener:
        return []

    return [_rec(
        "P006", "pacing",
        f"On {_DAY_NAMES[target_day]}s you typically open with "
        f"{typical_opener.value.replace('_', ' ')}. Today's opener is "
        f"{current_opener.value.replace('_', ' ')} — is this intentional?",
        severity="tip",
        impact=0.40,
        confidence=confidence,
    )]


# ---------------------------------------------------------------------------
# P007 — Programme duration consistency
# ---------------------------------------------------------------------------

def _p007(
    history: list[dict],
    current: RunSheetResponse,
    confidence: str,
) -> list[Recommendation]:
    target_type = current.programme_input.programme_type.value
    same_type = [h for h in history if h["programme_type"] == target_type]
    if len(same_type) < 3:
        return []

    typical = mean(h["total_duration_minutes"] for h in same_type)
    if typical <= 0:
        return []

    current_dur = current.programme_input.total_duration_minutes
    deviation = abs(current_dur - typical) / typical
    if deviation < 0.20:
        return []

    direction = "longer" if current_dur > typical else "shorter"
    return [_rec(
        "P007", "pacing",
        f"Your {target_type.replace('_', ' ')} shows typically run "
        f"{_format_minutes(typical)} minutes. Today's {current_dur}-minute show is "
        f"{direction} than usual.",
        severity="tip",
        impact=0.40,
        confidence=confidence,
    )]


# ---------------------------------------------------------------------------
# P008 — Smart Defaults
# ---------------------------------------------------------------------------

def _p008(
    history: list[dict],
    current: RunSheetResponse,
    user: User | None,
    confidence: str,
) -> list[Recommendation]:
    if len(history) < 5:
        return []
    if user is None:
        return []

    has_defaults = bool(
        user.default_station_name
        or user.default_presenter_name
        or user.default_programme_type
        or user.default_duration_minutes
        or user.default_talk_music_preference
    )
    if has_defaults:
        return []

    prog_types = Counter(h["programme_type"] for h in history)
    durations  = Counter(h["total_duration_minutes"] for h in history)
    prefs      = Counter(h["programme_input"].talk_music_preference.value for h in history)

    most_type = prog_types.most_common(1)[0][0] if prog_types else None
    most_dur  = durations.most_common(1)[0][0] if durations else None
    most_pref = prefs.most_common(1)[0][0] if prefs else None

    return [_rec(
        "P008", "pacing",
        f"Based on your last {len(history)} run-sheets, your typical setup is "
        f"{(most_type or 'n/a').replace('_', ' ')} / {most_dur or 'n/a'} min / "
        f"{(most_pref or 'n/a').replace('_', ' ')}. Save these as defaults in "
        "Settings to speed up future run-sheets.",
        severity="tip",
        impact=0.35,
        confidence=confidence,
    )]
