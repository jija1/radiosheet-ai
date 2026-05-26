"""15 tests for the new recommendations engine (Session K1)."""
from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.ai.recommendations.cultural_calendar import get_holiday_for_date, get_weekly_pattern
from app.ai.recommendations.engine import generate_recommendations as engine_generate
from app.ai.recommendations.library import LIBRARY
from app.ai.recommendations.mood_advisor import get_mood_advice
from app.ai.scorer import generate_recommendations
from app.api.v1.runsheet.schemas import (
    ProgrammeInput,
    ProgrammeType,
    Recommendation,
    Segment,
    SegmentType,
    TalkMusicPreference,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seg(name: str, seg_type: SegmentType, start: str, duration: int) -> Segment:
    h, m = map(int, start.split(":"))
    end_mins = h * 60 + m + duration
    return Segment(
        id=str(uuid.uuid4()),
        name=name,
        type=seg_type,
        start_time=start,
        end_time=f"{end_mins // 60:02d}:{end_mins % 60:02d}",
        duration_minutes=duration,
        colour_hex="#000000",
        presenter_notes="",
    )


def _prog(
    programme_type: ProgrammeType = ProgrammeType.MORNING_SHOW,
    start_time: str = "06:00",
    duration: int = 60,
    broadcast_date: date = date(2026, 5, 20),  # Wednesday
) -> ProgrammeInput:
    return ProgrammeInput(
        programme_type=programme_type,
        station_name="Test FM",
        broadcast_date=broadcast_date,
        start_time=start_time,
        total_duration_minutes=duration,
        presenter_name="Test Presenter",
        max_advert_blocks_per_hour=3,
        talk_music_preference=TalkMusicPreference.BALANCED,
    )


# ---------------------------------------------------------------------------
# Test 1: Each new programme type triggers at least one type-specific recommendation
# ---------------------------------------------------------------------------

def test_new_programme_types_each_trigger_recommendation() -> None:
    """SPORTS_SHOW, TALK_SHOW, RELIGIOUS_SHOW, FARMER_SHOW each trigger ≥1 rec."""
    cases = [
        # Sports show: no phone-in → S006 fires
        (ProgrammeType.SPORTS_SHOW, "10:00", [
            _seg("Intro",   SegmentType.INTRO,  "10:00", 2),
            _seg("Talk",    SegmentType.TALK,   "10:02", 5),
            _seg("Music 1", SegmentType.MUSIC,  "10:07", 5),
            _seg("Close",   SegmentType.CLOSE,  "10:12", 3),
        ]),
        # Talk show: >20% music → T001 fires
        (ProgrammeType.TALK_SHOW, "09:00", [
            _seg("Intro",   SegmentType.INTRO,  "09:00", 2),
            _seg("Music 1", SegmentType.MUSIC,  "09:02", 10),
            _seg("Music 2", SegmentType.MUSIC,  "09:12", 10),
            _seg("Close",   SegmentType.CLOSE,  "09:22", 3),
        ]),
        # Religious show: no scripture → R002 fires
        (ProgrammeType.RELIGIOUS_SHOW, "08:00", [
            _seg("Praise Music", SegmentType.MUSIC,  "08:00", 10),
            _seg("Music 2",      SegmentType.MUSIC,  "08:10", 10),
            _seg("Close",        SegmentType.CLOSE,  "08:20", 5),
        ]),
        # Farmer show: outside ideal window → F001 fires
        (ProgrammeType.FARMER_SHOW, "10:00", [
            _seg("Intro",  SegmentType.INTRO,  "10:00", 2),
            _seg("Talk",   SegmentType.TALK,   "10:02", 10),
            _seg("Music",  SegmentType.MUSIC,  "10:12", 10),
            _seg("Close",  SegmentType.CLOSE,  "10:22", 3),
        ]),
    ]
    for prog_type, start, segs in cases:
        prog = _prog(programme_type=prog_type, start_time=start, duration=30)
        recs = engine_generate(segs, prog)
        assert len(recs) >= 1, (
            f"{prog_type.value} triggered no recommendations with {len(segs)} segments"
        )


# ---------------------------------------------------------------------------
# Test 2: Forced minimum is removed (empty input returns empty list)
# ---------------------------------------------------------------------------

def test_forced_minimum_removed_empty_input() -> None:
    """The new engine has no forced minimum — empty segments returns empty list."""
    prog = _prog(programme_type=ProgrammeType.NEWS_HOUR, start_time="12:00", duration=30)
    recs = engine_generate([], prog)
    assert recs == [], f"Expected [] for empty segments, got {len(recs)} recommendations"


# ---------------------------------------------------------------------------
# Test 3: Source field populated on every recommendation
# ---------------------------------------------------------------------------

def test_source_field_populated() -> None:
    segs = [
        _seg("Intro",   SegmentType.INTRO,   "06:00", 2),
        _seg("Music 1", SegmentType.MUSIC,   "06:02", 10),
        _seg("Talk",    SegmentType.TALK,    "06:12", 10),
        _seg("Close",   SegmentType.CLOSE,   "06:22", 3),
    ]
    prog = _prog()
    recs = engine_generate(segs, prog)
    assert len(recs) > 0, "Expected at least one recommendation"
    for rec in recs:
        assert isinstance(rec.source, str) and len(rec.source.strip()) > 0, (
            f"Recommendation '{rec.recommendation_id}' has empty source field"
        )


# ---------------------------------------------------------------------------
# Test 4: Confidence field is one of high/medium/low
# ---------------------------------------------------------------------------

def test_confidence_field_valid_values() -> None:
    segs = [
        _seg("Intro",   SegmentType.INTRO,   "06:00", 2),
        _seg("Music 1", SegmentType.MUSIC,   "06:02", 10),
        _seg("Talk",    SegmentType.TALK,    "06:12", 10),
        _seg("Close",   SegmentType.CLOSE,   "06:22", 3),
    ]
    prog = _prog()
    recs = engine_generate(segs, prog)
    valid = {"high", "medium", "low"}
    for rec in recs:
        assert rec.confidence in valid, (
            f"Recommendation '{rec.recommendation_id}' has invalid confidence '{rec.confidence}'"
        )


# ---------------------------------------------------------------------------
# Test 5: Severity field is one of critical/warning/suggestion/tip
# ---------------------------------------------------------------------------

def test_severity_field_valid_values() -> None:
    segs = [
        _seg("Intro",   SegmentType.INTRO,   "06:00", 2),
        _seg("Music 1", SegmentType.MUSIC,   "06:02", 10),
        _seg("Talk",    SegmentType.TALK,    "06:12", 10),
        _seg("Close",   SegmentType.CLOSE,   "06:22", 3),
    ]
    prog = _prog()
    recs = engine_generate(segs, prog)
    valid = {"critical", "warning", "suggestion", "tip"}
    for rec in recs:
        assert rec.severity in valid, (
            f"Recommendation '{rec.recommendation_id}' has invalid severity '{rec.severity}'"
        )


# ---------------------------------------------------------------------------
# Test 6: Mood advisor returns correct energy level per time slot
# ---------------------------------------------------------------------------

def test_mood_advisor_energy_levels() -> None:
    cases = [
        ("04:30", 0, "low_energy"),       # pre-dawn Monday
        ("07:00", 1, "building_energy"),  # morning Tuesday
        ("12:00", 2, "high_energy"),      # midday Wednesday
        ("15:30", 3, "moderate_energy"),  # afternoon Thursday
        ("18:00", 4, "high_energy"),      # evening drive Friday (not prayer time)
        ("21:00", 5, "mellow"),           # evening Saturday (not override window)
        ("10:00", 6, "gospel_focused"),   # Sunday morning
    ]
    for time_str, dow, expected_energy in cases:
        result = get_mood_advice(time_str, dow)
        assert result["energy_level"] == expected_energy, (
            f"At {time_str} (dow={dow}) expected '{expected_energy}', "
            f"got '{result['energy_level']}'"
        )


# ---------------------------------------------------------------------------
# Test 7: Cultural calendar returns correct holiday for known dates
# ---------------------------------------------------------------------------

def test_cultural_calendar_known_holidays() -> None:
    assert get_holiday_for_date(date(2026, 12, 25)) == "Christmas Day"
    assert get_holiday_for_date(date(2026,  3,  6)) == "Independence Day"
    assert get_holiday_for_date(date(2026,  1,  1)) == "New Year's Day"
    assert get_holiday_for_date(date(2026,  5,  1)) == "Workers' Day"
    # Non-holiday
    assert get_holiday_for_date(date(2026,  5, 20)) is None
    # Farmers' Day: first Friday of December
    assert get_holiday_for_date(date(2026, 12,  4)) == "Farmers' Day"


# ---------------------------------------------------------------------------
# Test 8: Sunday morning triggers gospel/cultural recommendation
# ---------------------------------------------------------------------------

def test_sunday_morning_triggers_gospel_recommendation() -> None:
    # May 17, 2026 is a Sunday
    sunday = date(2026, 5, 17)
    prog = _prog(
        programme_type=ProgrammeType.MORNING_SHOW,
        start_time="07:00",
        broadcast_date=sunday,
        duration=60,
    )
    segs = [
        _seg("Intro",   SegmentType.INTRO,  "07:00", 2),
        _seg("Music 1", SegmentType.MUSIC,  "07:02", 10),
        _seg("Talk",    SegmentType.TALK,   "07:12", 10),
        _seg("Close",   SegmentType.CLOSE,  "07:22", 3),
    ]
    # Use conflict detector C010 which also handles Sunday morning
    from app.ai.conflict_detector import detect_conflicts
    conflicts = detect_conflicts(segs, prog, user_settings={"cultural_calendar_enabled": True})
    c010 = [c for c in conflicts if c.rule_id == "C010"]
    assert len(c010) >= 1, "C010 should fire for Sunday morning non-religious programme"


# ---------------------------------------------------------------------------
# Test 9: Drive time talk over 5 min triggers C008
# ---------------------------------------------------------------------------

def test_drive_time_talk_over_5_min_triggers_c008() -> None:
    from app.ai.conflict_detector import detect_conflicts
    prog = _prog(programme_type=ProgrammeType.DRIVE_TIME, start_time="16:00", duration=60)
    segs = [
        _seg("Intro",  SegmentType.INTRO,  "16:00",  2),
        _seg("Talk",   SegmentType.TALK,   "16:02",  6),   # 6 min > 5-min drive-time limit
        _seg("Music",  SegmentType.MUSIC,  "16:08", 10),
        _seg("Close",  SegmentType.CLOSE,  "16:18",  2),
    ]
    conflicts = detect_conflicts(segs, prog)
    c008 = [c for c in conflicts if c.rule_id == "C008"]
    assert len(c008) >= 1, "C008 should fire for 6-min talk in drive time without engagement"


# ---------------------------------------------------------------------------
# Test 10: Morning show missing weather in first 15 min triggers recommendation
# ---------------------------------------------------------------------------

def test_morning_show_missing_weather_triggers_recommendation() -> None:
    prog = _prog(programme_type=ProgrammeType.MORNING_SHOW, start_time="06:00", duration=30)
    segs = [
        _seg("Intro",   SegmentType.INTRO,      "06:00", 2),
        _seg("Sid",     SegmentType.STATION_ID, "06:02", 1),
        _seg("Music 1", SegmentType.MUSIC,      "06:03", 5),
        _seg("Talk",    SegmentType.TALK,        "06:08", 5),
        _seg("Advert",  SegmentType.ADVERT,     "06:13", 3),
        _seg("Close",   SegmentType.CLOSE,      "06:16", 2),
    ]
    recs = engine_generate(segs, prog)
    weather_recs = [r for r in recs if r.recommendation_id == "M001"]
    assert len(weather_recs) == 1, (
        "M001 (weather missing in first 15 min) should fire for morning show without weather"
    )


# ---------------------------------------------------------------------------
# Test 11: Sports show talk over 4 min without engagement triggers recommendation
# ---------------------------------------------------------------------------

def test_sports_show_long_talk_without_engagement_triggers() -> None:
    prog = _prog(programme_type=ProgrammeType.SPORTS_SHOW, start_time="14:00", duration=60)
    segs = [
        _seg("Intro",   SegmentType.INTRO,  "14:00",  2),
        _seg("Talk 1",  SegmentType.TALK,   "14:02",  5),  # 5 min > 4-min sports limit
        _seg("Music",   SegmentType.MUSIC,  "14:07",  5),  # no engagement within 3 min
        _seg("Talk 2",  SegmentType.TALK,   "14:12", 10),
        _seg("Close",   SegmentType.CLOSE,  "14:22",  3),
    ]
    recs = engine_generate(segs, prog)
    s001_recs = [r for r in recs if r.recommendation_id == "S001"]
    assert len(s001_recs) == 1, (
        "S001 should fire for sports show talk over 4 min without nearby engagement"
    )


# ---------------------------------------------------------------------------
# Test 12: Farmer show outside 04:00-07:00 triggers C006
# ---------------------------------------------------------------------------

def test_farmer_show_outside_window_triggers_c006() -> None:
    from app.ai.conflict_detector import detect_conflicts
    prog = _prog(programme_type=ProgrammeType.FARMER_SHOW, start_time="10:00", duration=30)
    segs = [
        _seg("Intro",  SegmentType.INTRO, "10:00", 2),
        _seg("Talk",   SegmentType.TALK,  "10:02", 10),
        _seg("Close",  SegmentType.CLOSE, "10:12",  3),
    ]
    conflicts = detect_conflicts(segs, prog)
    c006 = [c for c in conflicts if c.rule_id == "C006"]
    assert len(c006) == 1, "C006 should fire for farmer show starting at 10:00 (outside ideal window)"


# ---------------------------------------------------------------------------
# Test 13: Music-only with low local content triggers recommendation
# ---------------------------------------------------------------------------

def test_music_only_low_local_content_triggers_recommendation() -> None:
    prog = _prog(programme_type=ProgrammeType.MUSIC_ONLY, start_time="10:00", duration=30)
    segs = [
        _seg("Pop Track 1",   SegmentType.MUSIC,  "10:00",  4),
        _seg("Pop Track 2",   SegmentType.MUSIC,  "10:04",  4),
        _seg("Station ID",    SegmentType.STATION_ID, "10:08", 1),
        _seg("Pop Track 3",   SegmentType.MUSIC,  "10:09",  4),
        _seg("Advert",        SegmentType.ADVERT, "10:13",  2),
        _seg("Pop Track 4",   SegmentType.MUSIC,  "10:15",  4),
        _seg("Station ID 2",  SegmentType.STATION_ID, "10:19", 1),
        _seg("Pop Track 5",   SegmentType.MUSIC,  "10:20",  4),
        _seg("Advert 2",      SegmentType.ADVERT, "10:24",  2),
        _seg("Close",         SegmentType.CLOSE,  "10:26",  4),
    ]
    # None of the music segments have "highlife"/"local"/"ghana"/"afro" in name
    recs = engine_generate(segs, prog)
    mu003_recs = [r for r in recs if r.recommendation_id == "MU003"]
    assert len(mu003_recs) == 1, (
        "MU003 should fire for music-only with no local music keywords in segment names"
    )


# ---------------------------------------------------------------------------
# Test 14: Recommendations sorted by severity then impact_score descending
# ---------------------------------------------------------------------------

def test_recommendations_sorted_by_severity_then_impact() -> None:
    segs = [
        _seg("Intro",   SegmentType.INTRO,   "06:00", 2),
        _seg("Music 1", SegmentType.MUSIC,   "06:02", 10),
        _seg("Talk",    SegmentType.TALK,    "06:12", 10),
        _seg("Close",   SegmentType.CLOSE,   "06:22", 3),
    ]
    prog = _prog()
    recs = engine_generate(segs, prog)
    if len(recs) < 2:
        pytest.skip("Need >= 2 recommendations to test sort order")

    _SEVERITY_ORDER = {"critical": 0, "warning": 1, "suggestion": 2, "tip": 3}
    for i in range(len(recs) - 1):
        a, b = recs[i], recs[i + 1]
        ord_a = _SEVERITY_ORDER.get(a.severity, 99)
        ord_b = _SEVERITY_ORDER.get(b.severity, 99)
        if ord_a == ord_b:
            assert a.impact_score >= b.impact_score, (
                f"Within same severity '{a.severity}', expected impact descending: "
                f"{a.impact_score} >= {b.impact_score}"
            )
        else:
            assert ord_a <= ord_b, (
                f"Expected '{a.severity}' before '{b.severity}' in sort order"
            )


# ---------------------------------------------------------------------------
# Test 15: Recommendation IDs are unique across the library
# ---------------------------------------------------------------------------

def test_recommendation_ids_unique_across_library() -> None:
    ids = [entry["id"] for entry in LIBRARY]
    assert len(ids) == len(set(ids)), (
        f"Duplicate recommendation IDs found in library: "
        f"{[i for i in ids if ids.count(i) > 1]}"
    )
