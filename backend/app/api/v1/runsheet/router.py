from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.runsheet import service
from app.api.v1.runsheet.schemas import ProgrammeInput, RunSheetResponse
from app.api.v1.runsheet.service import RunSheetSummary
from app.dependencies import get_current_user, get_db
from app.models.user import User

router = APIRouter()


@router.post("/generate", response_model=RunSheetResponse)
async def generate(
    payload: ProgrammeInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunSheetResponse:
    return await service.generate_runsheet(payload, db, user_id=current_user.id)


@router.get("/history", response_model=list[RunSheetSummary])
async def history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RunSheetSummary]:
    return await service.get_history(db, user_id=current_user.id)


@router.get("/{runsheet_id}", response_model=RunSheetResponse)
async def get_runsheet(
    runsheet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunSheetResponse:
    return await service.get_by_id(runsheet_id, db, user_id=current_user.id)
