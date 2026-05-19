from __future__ import annotations

from pydantic import BaseModel


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
