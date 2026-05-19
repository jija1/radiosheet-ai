from __future__ import annotations

from pydantic import BaseModel, Field


class RunSheetRecordSummary(BaseModel):
    runsheet_id: str
    programme_type: str
    station_name: str
    broadcast_date: str
    generated_at: str
    conflict_count: int
    score: float


class DashboardResponse(BaseModel):
    total_runsheets: int
    recent_runsheets: list[RunSheetRecordSummary]
    average_score: float
    total_conflicts_resolved: int


class AuditLogEntry(BaseModel):
    action: str
    detail: str
    created_at: str


class UserInfo(BaseModel):
    email: str
    created_at: str


class ProfileStats(BaseModel):
    total_runsheets: int
    average_score: float
    total_conflicts_resolved: int


class ProfileResponse(BaseModel):
    email: str
    display_name: str | None
    created_at: str
    last_login: str | None
    stats: ProfileStats


class ProfileUpdateRequest(BaseModel):
    display_name: str = Field(max_length=100)
