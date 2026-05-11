from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.runsheet.models import RunSheetRecord
from app.api.v1.runsheet.schemas import RunSheetStats, Segment
from app.core.exceptions import NotFoundException
from app.dependencies import get_db

router = APIRouter()


class PreviewRequest(BaseModel):
    runsheet_id: str


class PreviewResponse(BaseModel):
    runsheet_id: str
    station_name: str
    programme_type: str
    presenter_name: str
    total_duration_minutes: int
    generated_at: str
    segments: list[Segment]
    stats: RunSheetStats


@router.post("/preview", response_model=PreviewResponse)
async def preview(
    payload: PreviewRequest,
    db: Session = Depends(get_db),
) -> PreviewResponse:
    record = db.query(RunSheetRecord).filter(RunSheetRecord.id == payload.runsheet_id).first()
    if not record:
        raise NotFoundException(f"Run-sheet '{payload.runsheet_id}' not found")

    segments = [Segment(**s) for s in json.loads(record.segments_json)]
    stats = RunSheetStats(**json.loads(record.stats_json))

    return PreviewResponse(
        runsheet_id=record.id,
        station_name=record.station_name,
        programme_type=record.programme_type,
        presenter_name=record.presenter_name,
        total_duration_minutes=record.total_duration_minutes,
        generated_at=record.generated_at,
        segments=segments,
        stats=stats,
    )
