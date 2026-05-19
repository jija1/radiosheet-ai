from fastapi import APIRouter

from app.api.v1.auth.router import router as auth_router
from app.api.v1.conflicts.router import router as conflicts_router
from app.api.v1.export.router import router as export_router
from app.api.v1.runsheet.router import router as runsheet_router
from app.api.v1.user.router import router as user_router
from app.api.v1.validate.router import router as validate_router

router = APIRouter()

router.include_router(auth_router,     prefix="/auth",      tags=["auth"])
router.include_router(runsheet_router, prefix="/runsheet",  tags=["runsheet"])
router.include_router(conflicts_router, prefix="/conflicts", tags=["conflicts"])
router.include_router(export_router,   prefix="/export",    tags=["export"])
router.include_router(user_router,     prefix="/user",      tags=["user"])
router.include_router(validate_router, prefix="/validate",  tags=["validate"])
