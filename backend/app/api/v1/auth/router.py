from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.v1.auth import service
from app.api.v1.auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.core.limiter import limiter
from app.dependencies import get_db

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("5/minute")
async def register(
    request: Request,
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    return await service.register(payload, db)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    return await service.login(payload, db)
