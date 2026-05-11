import uuid
from datetime import date

import pytest

from app.ai.conflict_detector import apply_fix, detect_conflicts
from app.ai.scheduling_engine import generate
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

def _seg(
    name: str,
    seg_type: SegmentType,
    start: str,
    duration: int,
    seg_id: str | None = None,
) -> Segment:
    h, m = map(int, start.split(":"))
    end_mins = h * 60 + m + duration
    return Segment(
        id=seg_id or str(uuid.uuid4()),
        name=name,
        type=seg_type,
        start_time=start,
        end_time=f"{end_mins // 60:02d}:{end_mins % 60:02d}",
        duration_minutes=duration,
        colour_hex="#000000",
        presenter_notes="",
    )


def _prog(duration: int = 60) -> ProgrammeInput:
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


def _rule_ids(conflicts: list) -> list[str]:
    return [c.rule_id for c in conflicts]


# ---------------------------------------------------------------------------
# Clean run-sheet: zero conflicts
# ---------------------------------------------------------------------------

def test_clean_runsheet_no_conflicts() -> None:
    """Engine-generated 15-min show should produce zero conflicts."""
    prog = _prog(duration=15)
    segs = generate(prog)
    assert detect_conflicts(segs, prog) == []


# ---------------------------------------------------------------------------
# C001 — Consecutive advert blocks
# ---------------------------------------------------------------------------

def test_c001_consecutive_adverts_triggers() -> None:
    segs = [
        _seg("Intro",    SegmentType.INTRO,   "06:00", 2),
        _seg("Advert A", SegmentType.ADVERT,  "06:02", 3),
        _seg("Advert B", SegmentType.ADVERT,  "06:05", 3),
        _seg("Music",    SegmentType.MUSIC,   "06:08", 4),
        _seg("Close",    SegmentType.CLOSE,   "06:12", 2),
    ]
    c001 = [c for c in detect_conflicts(segs, _prog()) if c.rule_id == "C001"]
    assert len(c001) == 1


def test_c001_short_separator_still_triggers() -> None:
    """A 2-minute talk break does not qualify as separation (must be >= 3 min)."""
    segs = [
        _seg("Advert A", SegmentType.ADVERT, "06:00", 3),
        _seg("Talk",     SegmentType.TALK,   "06:03", 2),  # too short
        _seg("Advert B", SegmentType.ADVERT, "06:05", 3),
    ]
    assert any(c.rule_id == "C001" for c in detect_conflicts(segs, _prog()))


def test_c001_qualifying_separator_no_trigger() -> None:
    segs = [
        _seg("Advert A", SegmentType.ADVERT, "06:00", 3),
        _seg("Talk",     SegmentType.TALK,   "06:03", 4),  # >= 3 min
        _seg("Advert B", SegmentType.ADVERT, "06:07", 3),
    ]
    assert not any(c.rule_id == "C001" for c in detect_conflicts(segs, _prog()))


# ---------------------------------------------------------------------------
# C002 — Total duration overrun
# ---------------------------------------------------------------------------

def test_c002_overrun_triggers() -> None:
    prog = _prog(duration=20)
    segs = [
        _seg("Intro",   SegmentType.INTRO,  "06:00",  2),
        _seg("Music 1", SegmentType.MUSIC,  "06:02", 10),
        _seg("Music 2", SegmentType.MUSIC,  "06:12", 10),  # total=22 > 20+1
        _seg("Close",   SegmentType.CLOSE,  "06:22",  2),
    ]
    assert any(c.rule_id == "C002" for c in detect_conflicts(segs, prog))


def test_c002_within_limit_no_trigger() -> None:
    prog = _prog(duration=20)
    segs = [
        _seg("Intro",  SegmentType.INTRO, "06:00",  2),
        _seg("Music",  SegmentType.MUSIC, "06:02", 16),
        _seg("Close",  SegmentType.CLOSE, "06:18",  2),
    ]
    assert not any(c.rule_id == "C002" for c in detect_conflicts(segs, prog))


def test_c002_one_minute_over_limit_no_trigger() -> None:
    """Exactly 1 minute over is allowed (rule triggers only at > 1 min excess)."""
    prog = _prog(duration=20)
    segs = [
        _seg("Intro",  SegmentType.INTRO, "06:00",  2),
        _seg("Music",  SegmentType.MUSIC, "06:02", 17),  # total=21 = 20+1
        _seg("Close",  SegmentType.CLOSE, "06:19",  2),
    ]
    assert not any(c.rule_id == "C002" for c in detect_conflicts(segs, prog))


# ---------------------------------------------------------------------------
# C003 — Missing station identification
# ---------------------------------------------------------------------------

def test_c003_no_station_id_triggers() -> None:
    prog = _prog(duration=30)
    segs = [
        _seg("Intro", SegmentType.INTRO, "06:00",  2),
        _seg("Music", SegmentType.MUSIC, "06:02", 26),
        _seg("Close", SegmentType.CLOSE, "06:28",  2),
    ]
    assert any(c.rule_id == "C003" for c in detect_conflicts(segs, prog))


def test_c003_station_id_in_first_15_no_trigger() -> None:
    """15-min programme with station ID at minute 2 — only one window, satisfied."""
    prog = _prog(duration=15)
    segs = [
        _seg("Intro",      SegmentType.INTRO,      "06:00", 2),
        _seg("Station ID", SegmentType.STATION_ID, "06:02", 2),
        _seg("Music",      SegmentType.MUSIC,      "06:04", 9),
        _seg("Close",      SegmentType.CLOSE,      "06:13", 2),
    ]
    assert not any(c.rule_id == "C003" for c in detect_conflicts(segs, prog))


def test_c003_fix_suggests_minute_14() -> None:
    """When first window is missing station ID, suggested at_minute is 14."""
    segs = [_seg("Music", SegmentType.MUSIC, "06:00", 30)]
    prog = _prog(duration=30)
    c003 = [c for c in detect_conflicts(segs, prog) if c.rule_id == "C003"]
    first_window = next(c for c in c003 if c.suggested_fix["at_minute"] == 14)
    assert first_window is not None


# ---------------------------------------------------------------------------
# C004 — Excessive advert density
# ---------------------------------------------------------------------------

def test_c004_over_20_percent_triggers() -> None:
    prog = _prog(duration=20)
    # 5 min advert / 20 min = 25% > 20%
    segs = [
        _seg("Intro",  SegmentType.INTRO,  "06:00",  2),
        _seg("Advert", SegmentType.ADVERT, "06:02",  5),
        _seg("Music",  SegmentType.MUSIC,  "06:07", 11),
        _seg("Close",  SegmentType.CLOSE,  "06:18",  2),
    ]
    assert any(c.rule_id == "C004" for c in detect_conflicts(segs, prog))


def test_c004_exactly_20_percent_no_trigger() -> None:
    prog = _prog(duration=20)
    # 4 min advert / 20 min = 20% — not strictly greater than 20%
    segs = [
        _seg("Intro",  SegmentType.INTRO,  "06:00",  2),
        _seg("Advert", SegmentType.ADVERT, "06:02",  4),
        _seg("Music",  SegmentType.MUSIC,  "06:06", 12),
        _seg("Close",  SegmentType.CLOSE,  "06:18",  2),
    ]
    assert not any(c.rule_id == "C004" for c in detect_conflicts(segs, prog))


# ---------------------------------------------------------------------------
# C005 — Segment overlap
# ---------------------------------------------------------------------------

def test_c005_overlap_triggers() -> None:
    seg_b_id = str(uuid.uuid4())
    segs = [
        _seg("Music A", SegmentType.MUSIC, "06:00", 5),
        _seg("Music B", SegmentType.MUSIC, "06:03", 5, seg_id=seg_b_id),  # starts before A ends
    ]
    c005 = [c for c in detect_conflicts(segs, _prog()) if c.rule_id == "C005"]
    assert len(c005) == 1
    assert seg_b_id in c005[0].affected_segment_ids


def test_c005_sequential_no_trigger() -> None:
    segs = [
        _seg("Music A", SegmentType.MUSIC, "06:00", 5),
        _seg("Music B", SegmentType.MUSIC, "06:05", 5),
    ]
    assert not any(c.rule_id == "C005" for c in detect_conflicts(segs, _prog()))


# ---------------------------------------------------------------------------
# apply_fix — C001: inserts talk segment between adverts
# ---------------------------------------------------------------------------

def test_apply_fix_c001_inserts_talk() -> None:
    advert_a_id = str(uuid.uuid4())
    advert_b_id = str(uuid.uuid4())
    segs = [
        _seg("Intro",    SegmentType.INTRO,   "06:00", 2),
        _seg("Advert A", SegmentType.ADVERT,  "06:02", 3, seg_id=advert_a_id),
        _seg("Advert B", SegmentType.ADVERT,  "06:05", 3, seg_id=advert_b_id),
        _seg("Music",    SegmentType.MUSIC,   "06:08", 5),
        _seg("Close",    SegmentType.CLOSE,   "06:13", 2),
    ]
    prog = _prog()
    c001 = next(c for c in detect_conflicts(segs, prog) if c.rule_id == "C001")
    fixed = apply_fix(segs, c001, prog)

    talk_segs = [s for s in fixed if s.type == SegmentType.TALK]
    assert len(talk_segs) == 1
    assert talk_segs[0].duration_minutes == 3

    # No C001 remaining after fix
    assert not any(c.rule_id == "C001" for c in detect_conflicts(fixed, prog))


def test_apply_fix_c001_times_are_sequential() -> None:
    segs = [
        _seg("Intro",    SegmentType.INTRO,  "06:00", 2),
        _seg("Advert A", SegmentType.ADVERT, "06:02", 3),
        _seg("Advert B", SegmentType.ADVERT, "06:05", 3),
        _seg("Music",    SegmentType.MUSIC,  "06:08", 4),
        _seg("Close",    SegmentType.CLOSE,  "06:12", 2),
    ]
    prog = _prog()
    c001 = next(c for c in detect_conflicts(segs, prog) if c.rule_id == "C001")
    fixed = apply_fix(segs, c001, prog)

    for i in range(1, len(fixed)):
        assert fixed[i].start_time == fixed[i - 1].end_time, (
            f"Gap between '{fixed[i-1].name}' and '{fixed[i].name}'"
        )


# ---------------------------------------------------------------------------
# apply_fix — C005: shifts overlapping segment
# ---------------------------------------------------------------------------

def test_apply_fix_c005_shifts_segment() -> None:
    seg_b_id = str(uuid.uuid4())
    segs = [
        _seg("Music A", SegmentType.MUSIC, "06:00", 5),
        _seg("Music B", SegmentType.MUSIC, "06:03", 5, seg_id=seg_b_id),
    ]
    prog = _prog()
    c005 = next(c for c in detect_conflicts(segs, prog) if c.rule_id == "C005")
    fixed = apply_fix(segs, c005, prog)

    seg_b = next(s for s in fixed if s.id == seg_b_id)
    assert seg_b.start_time == "06:05"  # shifted to where Music A ends

    # No overlaps remain
    assert not any(c.rule_id == "C005" for c in detect_conflicts(fixed, prog))


def test_apply_fix_c005_cascades_forward() -> None:
    """Segments after the shifted one must also shift forward."""
    seg_b_id = str(uuid.uuid4())
    seg_c_id = str(uuid.uuid4())
    segs = [
        _seg("Music A", SegmentType.MUSIC, "06:00", 5),
        _seg("Music B", SegmentType.MUSIC, "06:03", 4, seg_id=seg_b_id),  # overlaps
        _seg("Music C", SegmentType.MUSIC, "06:07", 3, seg_id=seg_c_id),
    ]
    prog = _prog()
    c005 = next(c for c in detect_conflicts(segs, prog) if c.rule_id == "C005")
    fixed = apply_fix(segs, c005, prog)

    seg_c = next(s for s in fixed if s.id == seg_c_id)
    # After shift, B starts at 06:05 and ends 06:09, so C must start at 06:09
    assert seg_c.start_time == "06:09"
