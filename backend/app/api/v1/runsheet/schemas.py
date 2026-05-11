from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class ProgrammeType(str, Enum):
    MORNING_SHOW = "morning_show"
    DRIVE_TIME = "drive_time"
    NEWS_HOUR = "news_hour"
    MUSIC_ONLY = "music_only"


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


class FixedSegment(BaseModel):
    name: str = Field(max_length=100)
    type: SegmentType
    start_time: str | None = None
    duration_minutes: int = Field(ge=1, le=120)


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
    stats: RunSheetStats
    generated_at: str


class FixRequest(BaseModel):
    runsheet_id: str
    conflict_id: str


class FixResponse(BaseModel):
    updated_segments: list[Segment]
    remaining_conflicts: list[Conflict]
