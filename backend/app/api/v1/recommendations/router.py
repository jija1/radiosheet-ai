from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.recommendations.service import (
    SuggestionApplyResponse,
    apply_suggestion,
)
from app.dependencies import get_current_user, get_db
from app.models.user import User

router = APIRouter()


class SuggestionApplyRequest(BaseModel):
    runsheet_id:      str
    recommendation_id: str


@router.post("/apply", response_model=SuggestionApplyResponse)
async def apply_suggestion_endpoint(
    payload:      SuggestionApplyRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
) -> SuggestionApplyResponse:
    return await apply_suggestion(
        payload.runsheet_id,
        payload.recommendation_id,
        db,
    )
