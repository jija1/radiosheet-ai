"""10 tests for extended conflict rules C006–C010 (Session K1)."""
from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.ai.conflict_detector import detect_conflicts
from app.api.v1.runsheet.schemas import (
    ProgrammeInput,
    ProgrammeType,
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
    programme_type: ProgrammeType,
    start_time: str,
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


def _basic_segs(start: str, count: int = 3) -> list[Segment]:
    h, m = map(int, start.split(":"))
    segs = []
    cursor = h * 60 + m
    for i in range(count):
        seg_start = f"{cursor // 60:02d}:{cursor % 60:02d}"
        segs.append(_seg(f"Music {i+1}", SegmentType.MUSIC, seg_start, 5))
        cursor += 5
    return segs


# ---------------------------------------------------------------------------
# Test 1: C006 morning show at 15:00 triggers
# ---------------------------------------------------------------------------

def test_c006_morning_show_at_1500_triggers() -> None:
    prog = _prog(ProgrammeType.MORNING_SHOW, "15:00", duration=30)
    segs = _basic_segs("15:00")
    conflicts = detect_conflicts(segs, prog)
    c006 = [c for c in conflicts if c.rule_id == "C006"]
    assert len(c006) == 1, (
        "C006 should trigger: morning show at 15:00 is outside 04:00–10:00 window"
    )


# ---------------------------------------------------------------------------
# Test 2: C006 drive time at 11:00 triggers
# ---------------------------------------------------------------------------

def test_c006_drive_time_at_1100_triggers() -> None:
    prog = _prog(ProgrammeType.DRIVE_TIME, "11:00", duration=30)
    segs = _basic_segs("11:00")
    conflicts = detect_conflicts(segs, prog)
    c006 = [c for c in conflicts if c.rule_id == "C006"]
    assert len(c006) == 1, (
        "C006 should trigger: drive time at 11:00 is outside 06:00–09:00 or 15:00–19:00"
    )


# ---------------------------------------------------------------------------
# Test 3: C007 high-energy music at 05:00 triggers
# ---------------------------------------------------------------------------

def test_c007_music_before_0600_triggers() -> None:
    prog = _prog(ProgrammeType.MORNING_SHOW, "04:30", duration=60)
    segs = [
        _seg("Music 1", SegmentType.MUSIC, "04:30", 10),
        _seg("Music 2", SegmentType.MUSIC, "04:40", 10),
        _seg("Talk",    SegmentType.TALK,  "04:50", 10),
    ]
    conflicts = detect_conflicts(segs, prog)
    c007 = [c for c in conflicts if c.rule_id == "C007"]
    assert len(c007) == 1, (
        "C007 should trigger: music segments scheduled before 06:00"
    )


# ---------------------------------------------------------------------------
# Test 4: C008 5-min talk in drive time without engagement triggers
# ---------------------------------------------------------------------------

def test_c008_drive_time_talk_5min_without_engagement_triggers() -> None:
    prog = _prog(ProgrammeType.DRIVE_TIME, "16:00", duration=60)
    segs = [
        _seg("Intro",  SegmentType.INTRO,  "16:00",  2),
        _seg("Talk",   SegmentType.TALK,   "16:02",  6),  # > 5 min, no engagement after
        _seg("Music",  SegmentType.MUSIC,  "16:08", 10),
        _seg("Close",  SegmentType.CLOSE,  "16:18",  2),
    ]
    conflicts = detect_conflicts(segs, prog)
    c008 = [c for c in conflicts if c.rule_id == "C008"]
    assert len(c008) >= 1, "C008 should fire for 6-min talk in drive time without engagement"


# ---------------------------------------------------------------------------
# Test 5: C008 same talk with vox_pop within 3 min does NOT trigger
# ---------------------------------------------------------------------------

def test_c008_talk_with_nearby_vox_pop_does_not_trigger() -> None:
    prog = _prog(ProgrammeType.DRIVE_TIME, "16:00", duration=60)
    segs = [
        _seg("Intro",   SegmentType.INTRO,     "16:00",  2),
        _seg("Talk",    SegmentType.TALK,      "16:02",  6),  # > 5 min
        _seg("Vox Pop", SegmentType.VOX_POP,  "16:08",  2),  # within 3 min of talk end
        _seg("Music",   SegmentType.MUSIC,    "16:10", 10),
        _seg("Close",   SegmentType.CLOSE,    "16:20",  2),
    ]
    conflicts = detect_conflicts(segs, prog)
    c008 = [c for c in conflicts if c.rule_id == "C008"]
    assert len(c008) == 0, (
        "C008 should NOT fire when a vox_pop starts within 3 minutes of the talk ending"
    )


# ---------------------------------------------------------------------------
# Test 6: C009 morning show with no engagement in 06:30-09:00 triggers
# ---------------------------------------------------------------------------

def test_c009_morning_show_no_peak_engagement_triggers() -> None:
    prog = _prog(ProgrammeType.MORNING_SHOW, "06:00", duration=120)
    segs = [
        _seg("Intro",   SegmentType.INTRO,  "06:00",  2),
        _seg("Music 1", SegmentType.MUSIC,  "06:02", 20),
        _seg("Talk",    SegmentType.TALK,   "06:22", 20),
        _seg("Music 2", SegmentType.MUSIC,  "06:42", 20),
        _seg("Advert",  SegmentType.ADVERT, "07:02",  3),
        _seg("Music 3", SegmentType.MUSIC,  "07:05", 20),
        _seg("Close",   SegmentType.CLOSE,  "07:25",  5),
    ]
    conflicts = detect_conflicts(segs, prog)
    c009 = [c for c in conflicts if c.rule_id == "C009"]
    assert len(c009) >= 1, (
        "C009 should trigger: morning show spanning 06:30-09:00 with no engagement segment"
    )


# ---------------------------------------------------------------------------
# Test 7: C010 Sunday morning without gospel triggers when cultural calendar enabled
# ---------------------------------------------------------------------------

def test_c010_sunday_morning_triggers_when_calendar_enabled() -> None:
    # May 17, 2026 is a Sunday
    sunday = date(2026, 5, 17)
    prog = _prog(ProgrammeType.MORNING_SHOW, "07:00", duration=60, broadcast_date=sunday)
    segs = [
        _seg("Intro",   SegmentType.INTRO,  "07:00",  2),
        _seg("Music 1", SegmentType.MUSIC,  "07:02", 20),
        _seg("Talk",    SegmentType.TALK,   "07:22", 20),
        _seg("Close",   SegmentType.CLOSE,  "07:42",  3),
    ]
    conflicts = detect_conflicts(segs, prog, user_settings={"cultural_calendar_enabled": True})
    c010 = [c for c in conflicts if c.rule_id == "C010"]
    assert len(c010) >= 1, (
        "C010 should trigger for Sunday morning non-religious programme with calendar enabled"
    )


# ---------------------------------------------------------------------------
# Test 8: C010 does NOT trigger when cultural_calendar disabled
# ---------------------------------------------------------------------------

def test_c010_does_not_trigger_when_calendar_disabled() -> None:
    sunday = date(2026, 5, 17)
    prog = _prog(ProgrammeType.MORNING_SHOW, "07:00", duration=60, broadcast_date=sunday)
    segs = [
        _seg("Intro",   SegmentType.INTRO,  "07:00",  2),
        _seg("Music 1", SegmentType.MUSIC,  "07:02", 20),
        _seg("Talk",    SegmentType.TALK,   "07:22", 20),
        _seg("Close",   SegmentType.CLOSE,  "07:42",  3),
    ]
    conflicts = detect_conflicts(segs, prog, user_settings={"cultural_calendar_enabled": False})
    c010 = [c for c in conflicts if c.rule_id == "C010"]
    assert len(c010) == 0, "C010 should NOT trigger when cultural_calendar_enabled is False"


# ---------------------------------------------------------------------------
# Test 9: C010 Christmas Day without acknowledgement triggers
# ---------------------------------------------------------------------------

def test_c010_christmas_day_without_acknowledgement_triggers() -> None:
    christmas = date(2026, 12, 25)
    prog = _prog(ProgrammeType.MORNING_SHOW, "08:00", duration=60, broadcast_date=christmas)
    # No TALK, DRAMA, or SCRIPTED_REPORT segments → no acknowledgement
    segs = [
        _seg("Intro",   SegmentType.INTRO,  "08:00",  2),
        _seg("Music 1", SegmentType.MUSIC,  "08:02", 20),
        _seg("Advert",  SegmentType.ADVERT, "08:22",  3),
        _seg("Music 2", SegmentType.MUSIC,  "08:25", 20),
        _seg("Close",   SegmentType.CLOSE,  "08:45",  5),
    ]
    conflicts = detect_conflicts(segs, prog, user_settings={"cultural_calendar_enabled": True})
    c010 = [c for c in conflicts if c.rule_id == "C010"]
    assert len(c010) >= 1, (
        "C010 should trigger on Christmas Day when there is no acknowledgement segment"
    )


# ---------------------------------------------------------------------------
# Test 10: All existing C001–C005 tests still pass (regression guard)
# ---------------------------------------------------------------------------

def test_c001_to_c005_still_work() -> None:
    """Regression: C001–C005 still fire correctly after adding C006–C010."""
    prog = _prog(ProgrammeType.MORNING_SHOW, "06:00", duration=60)

    # C001: consecutive adverts
    segs_c001 = [
        _seg("Advert A", SegmentType.ADVERT, "06:00", 3),
        _seg("Advert B", SegmentType.ADVERT, "06:03", 3),
    ]
    conflicts = detect_conflicts(segs_c001, prog)
    assert any(c.rule_id == "C001" for c in conflicts), "C001 should still fire"

    # C002: duration overrun
    segs_c002 = [_seg("Long Music", SegmentType.MUSIC, "06:00", 70)]  # 70 > 60 + 1
    conflicts = detect_conflicts(segs_c002, prog)
    assert any(c.rule_id == "C002" for c in conflicts), "C002 should still fire"

    # C003: missing station ID
    segs_c003 = [_seg("Music 1", SegmentType.MUSIC, "06:00", 30)]
    conflicts = detect_conflicts(segs_c003, prog)
    assert any(c.rule_id == "C003" for c in conflicts), "C003 should still fire"

    # C004: excessive advert density (>20% of 60 min = >12 min)
    segs_c004 = [
        _seg("Music",    SegmentType.MUSIC,  "06:00", 45),
        _seg("Advert 1", SegmentType.ADVERT, "06:45",  8),
        _seg("Advert 2", SegmentType.ADVERT, "06:53",  7),
    ]
    conflicts = detect_conflicts(segs_c004, prog)
    assert any(c.rule_id == "C004" for c in conflicts), "C004 should still fire"

    # C005: segment overlap
    segs_c005 = [
        _seg("Music A", SegmentType.MUSIC, "06:00", 10),
        _seg("Music B", SegmentType.MUSIC, "06:05",  5),  # starts before prev ends
    ]
    conflicts = detect_conflicts(segs_c005, prog)
    assert any(c.rule_id == "C005" for c in conflicts), "C005 should still fire"
