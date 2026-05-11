from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.runsheet import service
from app.api.v1.runsheet.schemas import ProgrammeInput, RunSheetResponse
from app.api.v1.runsheet.service import RunSheetSummary
from app.dependencies import get_db

router = APIRouter()


@router.post("/generate", response_model=RunSheetResponse)
async def generate(payload: ProgrammeInput, db: Session = Depends(get_db)) -> RunSheetResponse:
    return await service.generate_runsheet(payload, db)


@router.get("/history", response_model=list[RunSheetSummary])
async def history(db: Session = Depends(get_db)) -> list[RunSheetSummary]:
    return await service.get_history(db)


@router.get("/{runsheet_id}", response_model=RunSheetResponse)
async def get_runsheet(runsheet_id: str, db: Session = Depends(get_db)) -> RunSheetResponse:
    return await service.get_by_id(runsheet_id, db)
