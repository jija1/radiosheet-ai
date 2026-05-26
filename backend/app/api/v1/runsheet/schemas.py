from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ProgrammeType(str, Enum):
    MORNING_SHOW = "morning_show"
    DRIVE_TIME = "drive_time"
    NEWS_HOUR = "news_hour"
    MUSIC_ONLY = "music_only"
    SPORTS_SHOW = "sports_show"
    TALK_SHOW = "talk_show"
    RELIGIOUS_SHOW = "religious_show"
    FARMER_SHOW = "farmer_show"


class TalkMusicPreference(str, Enum):
    HEAVY_MUSIC = "heavy_music"
    BALANCED = "balanced"
    TALK_HEAVY = "talk_heavy"


class SegmentType(str, Enum):
    MUSIC = "music"
    TALK = "talk"
    ADVERT = "advert"
    NEWS = "news"
    STATION_ID = "station_id"
    WEATHER = "weather"
    CLOSE = "close"
    INTRO = "intro"
    SIG_TUNE = "sig_tune"
    INTERVIEW = "interview"
    VOX_POP = "vox_pop"
    PHONE_IN_SEGMENT = "phone_in_segment"
    DRAMA = "drama"
    STORYTELLING = "storytelling"
    SPONSOR = "sponsor"
    SCRIPTED_REPORT = "scripted_report"


class FixedSegment(BaseModel):
    name: str = Field(max_length=100)
    type: SegmentType
    start_time: str | None = None
    duration_minutes: int = Field(ge=1, le=120)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v


class ProgrammeInput(BaseModel):
    programme_type: ProgrammeType
    station_name: str = Field(max_length=100)
    broadcast_date: date
    start_time: str
    total_duration_minutes: int = Field(ge=15, le=240)
    presenter_name: str = Field(max_length=100)
    max_advert_blocks_per_hour: int = Field(ge=1, le=6, default=3)
    fixed_segments: list[FixedSegment] = []
    talk_music_preference: TalkMusicPreference = TalkMusicPreference.BALANCED

    @field_validator("station_name", "presenter_name", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v


class Segment(BaseModel):
    id: str
    name: str
    type: SegmentType
    start_time: str
    end_time: str
    duration_minutes: int
    colour_hex: str
    presenter_notes: str = ""


class Conflict(BaseModel):
    rule_id: str
    severity: str
    message: str
    affected_segment_ids: list[str]
    suggested_fix: dict


class Recommendation(BaseModel):
    category: str
    message: str
    impact_score: float
    source: str = "industry best practice"
    confidence: str = "medium"
    severity: str = "suggestion"
    based_on_history: bool = False
    recommendation_id: str = ""


class ComplianceViolation(BaseModel):
    rule_id: str
    severity: str
    message: str
    penalty: int


class ComplianceResult(BaseModel):
    compliance_score: int
    compliance_risk: str
    compliance_violations: list[ComplianceViolation]


class RunSheetStats(BaseModel):
    total_segments: int
    total_duration_minutes: int
    music_percentage: float
    talk_percentage: float
    advert_percentage: float
    conflict_count: int
    score: float


class RunSheetResponse(BaseModel):
    runsheet_id: str
    programme_input: ProgrammeInput
    segments: list[Segment]
    conflicts: list[Conflict]
    recommendations: list[Recommendation]
    compliance_score: int
    compliance_risk: str
    compliance_violations: list[ComplianceViolation]
    stats: RunSheetStats
    generated_at: str


class FixRequest(BaseModel):
    runsheet_id: str
    conflict_id: str


class FixResponse(BaseModel):
    updated_segments: list[Segment]
    remaining_conflicts: list[Conflict]
    compliance_score: int
    compliance_risk: str
    compliance_violations: list[ComplianceViolation]


class UpdateSegmentsRequest(BaseModel):
    runsheet_id: str
    segments: list[Segment]


class UpdateSegmentsResponse(BaseModel):
    segments: list[Segment]
    conflicts: list[Conflict]
    stats: RunSheetStats
    compliance_score: int
    compliance_risk: str
    compliance_violations: list[ComplianceViolation]
