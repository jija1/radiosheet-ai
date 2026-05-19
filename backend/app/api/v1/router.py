from fastapi import APIRouter

from app.api.v1.auth.router import router as auth_router
from app.api.v1.conflicts.router import router as conflicts_router
from app.api.v1.export.router import router as export_router
from app.api.v1.runsheet.router import router as runsheet_router

router = APIRouter()

router.include_router(auth_router,     prefix="/auth",      tags=["auth"])
router.include_router(runsheet_router, prefix="/runsheet",  tags=["runsheet"])
router.include_router(conflicts_router, prefix="/conflicts", tags=["conflicts"])
router.include_router(export_router,   prefix="/export",    tags=["export"])
