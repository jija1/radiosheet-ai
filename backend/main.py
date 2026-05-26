from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from app.api.v1.router import router as v1_router
from app.core.limiter import limiter
from app.db.session import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RadioSheet AI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter

async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests, please try again later"},
    )

app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
app.include_router(v1_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"status": "ok", "service": "RadioSheet AI"}
