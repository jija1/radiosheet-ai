from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


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


class UserSettings(BaseModel):
    default_station_name: str | None = None
    default_presenter_name: str | None = None
    default_programme_type: str | None = None
    default_duration_minutes: int | None = None
    default_talk_music_preference: str | None = None
    default_max_adverts_per_hour: int | None = None
    time_format: str = "24h"
    cultural_calendar_enabled: bool = True
    strict_mode: bool = False
    auto_apply_fixes: bool = False
    notifications_enabled: bool = True
    default_region: str | None = None
    station_audience: str | None = None
    recommendation_depth: str = "standard"

    @field_validator("time_format")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        if v not in {"12h", "24h"}:
            raise ValueError("time_format must be '12h' or '24h'")
        return v

    @field_validator("recommendation_depth")
    @classmethod
    def validate_depth(cls, v: str) -> str:
        if v not in {"light", "standard", "detailed"}:
            raise ValueError("recommendation_depth must be 'light', 'standard', or 'detailed'")
        return v


class UserSettingsUpdate(BaseModel):
    default_station_name: str | None = None
    default_presenter_name: str | None = None
    default_programme_type: str | None = None
    default_duration_minutes: int | None = None
    default_talk_music_preference: str | None = None
    default_max_adverts_per_hour: int | None = None
    time_format: str | None = None
    cultural_calendar_enabled: bool | None = None
    strict_mode: bool | None = None
    auto_apply_fixes: bool | None = None
    notifications_enabled: bool | None = None
    default_region: str | None = None
    station_audience: str | None = None
    recommendation_depth: str | None = None
