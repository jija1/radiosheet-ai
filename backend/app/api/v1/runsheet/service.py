from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai import conflict_detector, notes_generator, scheduling_engine, scorer
from app.api.v1.runsheet.models import RunSheetRecord
from app.api.v1.runsheet.schemas import (
    Conflict,
    ProgrammeInput,
    Recommendation,
    RunSheetResponse,
    RunSheetStats,
    Segment,
    SegmentType,
)
from app.core.exceptions import NotFoundException


class RunSheetSummary(BaseModel):
    id: str
    station_name: str
    programme_type: str
    total_duration_minutes: int
    generated_at: str


# ---------------------------------------------------------------------------
# generate_runsheet
# ---------------------------------------------------------------------------

async def generate_runsheet(
    payload: ProgrammeInput,
    db: Session,
) -> RunSheetResponse:
    segments: list[Segment] = scheduling_engine.generate(payload)
    segments = notes_generator.generate_notes(segments, payload)
    conflicts: list[Conflict] = conflict_detector.detect_conflicts(segments, payload)
    recommendations: list[Recommendation]
    recommendations, score = scorer.generate_recommendations(segments, payload)
    stats = _compute_stats(segments, conflicts, score)

    runsheet_id  = str(uuid.uuid4())
    generated_at = datetime.now(timezone.utc).isoformat()

    record = RunSheetRecord(
        id=runsheet_id,
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

    return RunSheetResponse(
        runsheet_id=runsheet_id,
        programme_input=payload,
        segments=segments,
        conflicts=conflicts,
        recommendations=recommendations,
        stats=stats,
        generated_at=generated_at,
    )


# ---------------------------------------------------------------------------
# get_history
# ---------------------------------------------------------------------------

async def get_history(db: Session) -> list[RunSheetSummary]:
    records = (
        db.query(RunSheetRecord)
        .order_by(RunSheetRecord.generated_at.desc())
        .limit(20)
        .all()
    )
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

async def get_by_id(runsheet_id: str, db: Session) -> RunSheetResponse:
    record = db.query(RunSheetRecord).filter(RunSheetRecord.id == runsheet_id).first()
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

    return RunSheetResponse(
        runsheet_id=record.id,
        programme_input=programme_input,
        segments=segments,
        conflicts=conflicts,
        recommendations=recommendations,
        stats=stats,
        generated_at=record.generated_at,
    )


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
