from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.conflicts import service
from app.api.v1.runsheet.schemas import (
    Conflict,
    FixRequest,
    FixResponse,
    ProgrammeInput,
    Segment,
)
from app.dependencies import get_db

router = APIRouter()


class DetectRequest(BaseModel):
    segments: list[Segment]
    programme_input: ProgrammeInput


@router.post("/detect", response_model=list[Conflict])
async def detect(payload: DetectRequest) -> list[Conflict]:
    return await service.detect(payload.segments, payload.programme_input)


@router.post("/apply-fix", response_model=FixResponse)
async def apply_fix(
    payload: FixRequest,
    db: Session = Depends(get_db),
) -> FixResponse:
    return await service.apply_fix(payload.runsheet_id, payload.conflict_id, db)
