from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.auth import service
from app.api.v1.auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.dependencies import get_db

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    return await service.register(payload, db)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    return await service.login(payload, db)
