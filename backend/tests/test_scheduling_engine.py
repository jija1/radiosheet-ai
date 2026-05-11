import re
from datetime import date

import pytest

from app.ai.scheduling_engine import generate
from app.api.v1.runsheet.schemas import (
    ProgrammeInput,
    ProgrammeType,
    Segment,
    SegmentType,
    TalkMusicPreference,
)

HHMM_RE = re.compile(r"^\d{2}:\d{2}$")


def _morning_show_input(duration: int = 60) -> ProgrammeInput:
    return ProgrammeInput(
        programme_type=ProgrammeType.MORNING_SHOW,
        station_name="Test FM",
        broadcast_date=date(2026, 5, 11),
        start_time="06:00",
        total_duration_minutes=duration,
        presenter_name="Test Presenter",
        max_advert_blocks_per_hour=3,
        talk_music_preference=TalkMusicPreference.BALANCED,
    )


@pytest.fixture
def segments() -> list[Segment]:
    return generate(_morning_show_input())


def test_returns_list_of_segments(segments: list[Segment]) -> None:
    assert isinstance(segments, list)
    assert len(segments) > 0
    for seg in segments:
        assert isinstance(seg, Segment)


def test_total_duration_does_not_exceed_input(segments: list[Segment]) -> None:
    total = sum(s.duration_minutes for s in segments)
    assert total <= 60


def test_at_least_one_music_segment(segments: list[Segment]) -> None:
    types = [s.type for s in segments]
    assert SegmentType.MUSIC in types


def test_at_least_one_news_segment(segments: list[Segment]) -> None:
    types = [s.type for s in segments]
    assert SegmentType.NEWS in types


def test_all_times_in_hhmm_format(segments: list[Segment]) -> None:
    for seg in segments:
        assert HHMM_RE.match(seg.start_time), f"Bad start_time: {seg.start_time!r}"
        assert HHMM_RE.match(seg.end_time),   f"Bad end_time: {seg.end_time!r}"


def test_no_zero_duration_segments(segments: list[Segment]) -> None:
    for seg in segments:
        assert seg.duration_minutes > 0, f"Segment {seg.name!r} has duration 0"


def test_segments_are_sequential(segments: list[Segment]) -> None:
    """Each segment's start_time must equal the previous segment's end_time."""
    for i in range(1, len(segments)):
        assert segments[i].start_time == segments[i - 1].end_time, (
            f"Gap/overlap between '{segments[i-1].name}' and '{segments[i].name}'"
        )


def test_first_segment_matches_programme_start(segments: list[Segment]) -> None:
    assert segments[0].start_time == "06:00"


def test_station_id_within_first_15_minutes(segments: list[Segment]) -> None:
    """C003 pre-condition: a station ID must appear in the first 15 minutes."""
    start_minutes = 6 * 60  # 06:00
    for seg in segments:
        if seg.type == SegmentType.STATION_ID:
            seg_start = int(seg.start_time[:2]) * 60 + int(seg.start_time[3:])
            assert seg_start - start_minutes <= 15
            return
    pytest.fail("No STATION_ID segment found")


@pytest.mark.parametrize("duration", [15, 30, 120, 240])
def test_various_durations_stay_within_budget(duration: int) -> None:
    segs = generate(_morning_show_input(duration))
    total = sum(s.duration_minutes for s in segs)
    assert total <= duration
