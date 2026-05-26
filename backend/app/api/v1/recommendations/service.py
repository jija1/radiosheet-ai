"""
Apply-suggestion service for recommendation cards.

Maps recommendation_id values produced by the AI engine to automated
segment insertions, applies them, re-runs conflict detection, compliance
validation and the scorer, then persists and returns the updated state.
"""
from __future__ import annotations

import json
import uuid

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai import compliance_validator, conflict_detector, scorer
from app.api.v1.runsheet.models import RunSheetRecord
from app.api.v1.runsheet.schemas import (
    Conflict,
    ComplianceViolation,
    ProgrammeInput,
    Recommendation,
    Segment,
    SegmentType,
)
from app.core.exceptions import NotFoundException
from app.models.audit_log import log_action


# ---------------------------------------------------------------------------
# Helpers — duplicated locally so this module stays self-contained
# ---------------------------------------------------------------------------

def _hhmm_to_minutes(t: str) -> int:
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def _minutes_to_hhmm(minutes: int) -> str:
    minutes = max(0, minutes)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _recalculate_times(segments: list[Segment]) -> list[Segment]:
    if not segments:
        return segments
    result: list[Segment] = []
    cursor = _hhmm_to_minutes(segments[0].start_time)
    for seg in segments:
        new_start = _minutes_to_hhmm(cursor)
        new_end   = _minutes_to_hhmm(cursor + seg.duration_minutes)
        result.append(seg.model_copy(update={"start_time": new_start, "end_time": new_end}))
        cursor += seg.duration_minutes
    return result


# ---------------------------------------------------------------------------
# Segment metadata
# ---------------------------------------------------------------------------

_COLOURS: dict[SegmentType, str] = {
    SegmentType.WEATHER:          "#10b981",
    SegmentType.NEWS:             "#8b5cf6",
    SegmentType.STATION_ID:       "#06b6d4",
    SegmentType.PHONE_IN_SEGMENT: "#3b82f6",
    SegmentType.VOX_POP:          "#10b981",
}

_NAMES: dict[SegmentType, str] = {
    SegmentType.WEATHER:          "Weather Update",
    SegmentType.NEWS:             "News Bulletin",
    SegmentType.STATION_ID:       "Station ID",
    SegmentType.PHONE_IN_SEGMENT: "Phone-in Segment",
    SegmentType.VOX_POP:          "Vox Pop",
}

# ---------------------------------------------------------------------------
# Public: set of recommendation IDs that have automated fixes
# ---------------------------------------------------------------------------

FIXABLE_IDS: frozenset[str] = frozenset({
    "M001",  # missing weather → weather at +10 min
    "M002",  # no news before 07:00 → news at +20 min
    "M009",  # no station ID → station_id at +14 min
    "M006",  # no live engagement → phone-in at 07:00
    "C008",  # talk fatigue → vox_pop after long talk
    "C009",  # missing peak engagement → phone-in in peak window
})


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class SuggestionApplyResponse(BaseModel):
    updated_segments:      list[Segment]
    remaining_conflicts:   list[Conflict]
    compliance_score:      int
    compliance_risk:       str
    compliance_violations: list[ComplianceViolation]
    updated_recommendations: list[Recommendation]


# ---------------------------------------------------------------------------
# Fix builders
# ---------------------------------------------------------------------------

def _make_segment(seg_type: SegmentType, start_min: int, duration: int) -> Segment:
    end_min = start_min + duration
    return Segment(
        id=str(uuid.uuid4()),
        name=_NAMES.get(seg_type, seg_type.value.replace("_", " ").title()),
        type=seg_type,
        start_time=_minutes_to_hhmm(start_min),
        end_time=_minutes_to_hhmm(end_min),
        duration_minutes=duration,
        colour_hex=_COLOURS.get(seg_type, "#3b82f6"),
        presenter_notes="",
    )


def _insert_at_offset(
    segments: list[Segment],
    seg_type: SegmentType,
    duration: int,
    offset_from_start: int,
) -> list[Segment]:
    """Insert a new segment at *offset_from_start* minutes after programme start."""
    prog_start  = _hhmm_to_minutes(segments[0].start_time) if segments else 0
    target_abs  = prog_start + offset_from_start

    # Find the first segment that starts at or after the target time
    idx = len(segments)
    for i, seg in enumerate(segments):
        if _hhmm_to_minutes(seg.start_time) >= target_abs:
            idx = i
            break

    new_seg = _make_segment(seg_type, target_abs, duration)
    updated = list(segments)
    updated.insert(idx, new_seg)
    return _recalculate_times(updated)


def _insert_after_id(
    segments: list[Segment],
    after_id: str,
    seg_type: SegmentType,
    duration: int,
) -> list[Segment]:
    """Insert a new segment immediately after the segment whose id == after_id."""
    idx = next((i for i, s in enumerate(segments) if s.id == after_id), None)
    if idx is None:
        return list(segments)
    prev_end = _hhmm_to_minutes(segments[idx].end_time)
    new_seg  = _make_segment(seg_type, prev_end, duration)
    updated  = list(segments)
    updated.insert(idx + 1, new_seg)
    return _recalculate_times(updated)


# ---------------------------------------------------------------------------
# Fix dispatcher
# ---------------------------------------------------------------------------

def _apply_fix(
    rec_id:         str,
    segments:       list[Segment],
    conflicts:      list[Conflict],
    programme_input: ProgrammeInput,
) -> list[Segment]:
    prog_start = _hhmm_to_minutes(programme_input.start_time)

    if rec_id == "M001":
        return _insert_at_offset(segments, SegmentType.WEATHER, 3, 10)

    if rec_id == "M002":
        return _insert_at_offset(segments, SegmentType.NEWS, 5, 20)

    if rec_id == "M009":
        return _insert_at_offset(segments, SegmentType.STATION_ID, 2, 14)

    if rec_id == "M006":
        # Target 07:00 absolute, but clamp to within the programme
        seven_am_offset = max(0, 7 * 60 - prog_start)
        offset = min(seven_am_offset, programme_input.total_duration_minutes - 5)
        offset = max(0, offset)
        return _insert_at_offset(segments, SegmentType.PHONE_IN_SEGMENT, 3, offset)

    if rec_id == "C008":
        # Use the existing C008 conflict's after_segment_id if present
        c008 = next((c for c in conflicts if c.rule_id == "C008"), None)
        after_id = (c008.suggested_fix.get("after_segment_id") if c008 else None)
        if after_id:
            return _insert_after_id(segments, after_id, SegmentType.VOX_POP, 2)
        # Fallback: after the longest talk segment
        talk_segs = [s for s in segments if s.type == SegmentType.TALK]
        if talk_segs:
            longest = max(talk_segs, key=lambda s: s.duration_minutes)
            return _insert_after_id(segments, longest.id, SegmentType.VOX_POP, 2)
        return list(segments)

    if rec_id == "C009":
        # Insert phone-in at commute peak window start or programme start + 30 min
        is_drive = programme_input.programme_type.value == "drive_time"
        peak_abs = 16 * 60 + 30 if is_drive else 6 * 60 + 30
        offset   = max(0, peak_abs - prog_start)
        offset   = min(offset, programme_input.total_duration_minutes - 5)
        return _insert_at_offset(segments, SegmentType.PHONE_IN_SEGMENT, 3, max(0, offset))

    return list(segments)


# ---------------------------------------------------------------------------
# Public service function
# ---------------------------------------------------------------------------

async def apply_suggestion(
    runsheet_id:     str,
    recommendation_id: str,
    db:              Session,
) -> SuggestionApplyResponse:
    record = db.query(RunSheetRecord).filter(RunSheetRecord.id == runsheet_id).first()
    if not record:
        raise NotFoundException(f"Run-sheet '{runsheet_id}' not found")

    if recommendation_id not in FIXABLE_IDS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Recommendation '{recommendation_id}' has no automated fix",
        )

    segments       = [Segment(**s) for s in json.loads(record.segments_json)]
    conflicts      = [Conflict(**c) for c in json.loads(record.conflicts_json)]
    programme_input = ProgrammeInput(**json.loads(record.programme_input_json))

    updated_segments = _apply_fix(recommendation_id, segments, conflicts, programme_input)

    remaining_conflicts = conflict_detector.detect_conflicts(updated_segments, programme_input)
    comp                = compliance_validator.validate_compliance(updated_segments, programme_input)
    recs, _             = scorer.generate_recommendations(updated_segments, programme_input)

    # Persist updated state
    record.segments_json  = json.dumps([s.model_dump(mode="json") for s in updated_segments])
    record.conflicts_json = json.dumps([c.model_dump(mode="json") for c in remaining_conflicts])
    db.commit()

    log_action(
        db, record.user_id,
        "suggestion_applied",
        f"rec_id={recommendation_id}, runsheet={runsheet_id}",
    )

    return SuggestionApplyResponse(
        updated_segments=updated_segments,
        remaining_conflicts=remaining_conflicts,
        compliance_score=comp.compliance_score,
        compliance_risk=comp.compliance_risk,
        compliance_violations=comp.compliance_violations,
        updated_recommendations=recs,
    )
