from fastapi import APIRouter

router = APIRouter()

try:
    from app.api.v1.runsheet.router import router as runsheet_router
    router.include_router(runsheet_router, prefix="/runsheet", tags=["runsheet"])
except ImportError:
    pass

try:
    from app.api.v1.conflicts.router import router as conflicts_router
    router.include_router(conflicts_router, prefix="/conflicts", tags=["conflicts"])
except ImportError:
    pass

try:
    from app.api.v1.export.router import router as export_router
    router.include_router(export_router, prefix="/export", tags=["export"])
except ImportError:
    pass
