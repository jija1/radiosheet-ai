from __future__ import annotations

from pydantic import BaseModel

from app.api.v1.runsheet.schemas import (
    ComplianceViolation,
    Conflict,
    ProgrammeInput,
    Recommendation,
    RunSheetStats,
    Segment,
)


class ValidateRequest(BaseModel):
    segments: list[Segment]
    programme_input: ProgrammeInput


class ValidateResponse(BaseModel):
    segments: list[Segment]
    conflicts: list[Conflict]
    compliance_score: int
    compliance_risk: str
    compliance_violations: list[ComplianceViolation]
    stats: RunSheetStats
    recommendations: list[Recommendation]
