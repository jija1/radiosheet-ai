"""
10 pytest unit tests for compliance_validator (G001–G005).
Each test is self-contained and uses lightweight helper functions.
"""
from __future__ import annotations

import uuid
from datetime import date

from app.ai.compliance_validator import validate_compliance
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
    seg_type: SegmentType,
    start: str,
    duration: int,
) -> Segment:
    h, m = map(int, start.split(":"))
    end_mins = h * 60 + m + duration
    return Segment(
        id=str(uuid.uuid4()),
        name=seg_type.value.replace("_", " ").title(),
        type=seg_type,
        start_time=start,
        end_time=f"{end_mins // 60:02d}:{end_mins % 60:02d}",
        duration_minutes=duration,
        colour_hex="#000000",
        presenter_notes="",
    )


def _prog(
    duration: int = 60,
    start: str = "06:00",
    prog_type: ProgrammeType = ProgrammeType.MORNING_SHOW,
) -> ProgrammeInput:
    return ProgrammeInput(
        programme_type=prog_type,
        station_name="Test FM",
        broadcast_date=date(2026, 5, 1),
        start_time=start,
        total_duration_minutes=duration,
        presenter_name="Test Presenter",
        max_advert_blocks_per_hour=3,
        talk_music_preference=TalkMusicPreference.BALANCED,
    )


def _rule_ids(result) -> list[str]:
    return [v.rule_id for v in result.compliance_violations]


# ---------------------------------------------------------------------------
# Test 1 — Perfect run-sheet scores 100
# ---------------------------------------------------------------------------

def test_perfect_runsheet_scores_100():
    """No violations triggered: all G rules satisfied."""
    # 60-min MORNING_SHOW
    # Station IDs at offsets 0, 22, 47 → G001 and both G002 windows covered
    # 5 min adverts (8.3% < 20%) → G003 ok
    # Single advert block → G004 ok
    # No forbidden segment types → G005 ok
    segs = [
        _seg(SegmentType.STATION_ID, "06:00", 2),   # offset 0 → G001
        _seg(SegmentType.MUSIC,      "06:02", 20),
        _seg(SegmentType.STATION_ID, "06:22", 2),   # offset 22 → G002 (15-45)
        _seg(SegmentType.ADVERT,     "06:24", 5),
        _seg(SegmentType.TALK,       "06:29", 18),
        _seg(SegmentType.STATION_ID, "06:47", 2),   # offset 47 → G002 (45-60)
        _seg(SegmentType.MUSIC,      "06:49", 11),
    ]
    result = validate_compliance(segs, _prog(duration=60))

    assert result.compliance_score == 100
    assert result.compliance_risk == "compliant"
    assert result.compliance_violations == []


# ---------------------------------------------------------------------------
# Test 2 — Missing opening station ID triggers G001, score 90
# ---------------------------------------------------------------------------

def test_missing_opening_station_id_triggers_g001():
    """No station ID in first 15 min → G001, penalty -10, score 90."""
    # 30-min programme; station ID at offset 20 (outside 0-15 window)
    segs = [
        _seg(SegmentType.MUSIC,      "06:00", 10),
        _seg(SegmentType.TALK,       "06:10", 10),
        _seg(SegmentType.STATION_ID, "06:20", 2),   # offset 20 → satisfies G002 (15-30)
        _seg(SegmentType.MUSIC,      "06:22", 8),
    ]
    result = validate_compliance(segs, _prog(duration=30))

    assert "G001" in _rule_ids(result)
    assert result.compliance_score == 90
    assert result.compliance_risk == "compliant"


# ---------------------------------------------------------------------------
# Test 3 — Missing periodic station ID triggers G002, score 97
# ---------------------------------------------------------------------------

def test_missing_periodic_station_id_triggers_g002():
    """Station ID in opening window but not in the 15-45 window → G002, -3, score 97."""
    # 45-min programme: station ID at offset 0 (G001 ok), nothing in 15-45 window
    segs = [
        _seg(SegmentType.STATION_ID, "06:00", 2),   # offset 0 → G001 ok
        _seg(SegmentType.MUSIC,      "06:02", 40),  # no station ID in 15-45 window
        _seg(SegmentType.TALK,       "06:42", 3),
    ]
    result = validate_compliance(segs, _prog(duration=45))

    assert "G002" in _rule_ids(result)
    assert "G001" not in _rule_ids(result)
    assert result.compliance_score == 97


# ---------------------------------------------------------------------------
# Test 4 — Adverts over 20% triggers G003, score 75
# ---------------------------------------------------------------------------

def test_adverts_over_20_percent_triggers_g003():
    """15 min adverts in 60-min programme = 25% → G003, -25, score 75."""
    segs = [
        _seg(SegmentType.STATION_ID, "06:00", 2),   # G001 ok
        _seg(SegmentType.ADVERT,     "06:02", 15),  # 25% of 60 min
        _seg(SegmentType.STATION_ID, "06:17", 5),   # G002 (15-45) ok
        _seg(SegmentType.MUSIC,      "06:22", 25),
        _seg(SegmentType.STATION_ID, "06:47", 2),   # G002 (45-60) ok
        _seg(SegmentType.TALK,       "06:49", 11),
    ]
    result = validate_compliance(segs, _prog(duration=60))

    assert "G003" in _rule_ids(result)
    assert result.compliance_score == 75
    assert result.compliance_risk == "moderate"


# ---------------------------------------------------------------------------
# Test 5 — Advert blocks closer than 10 min triggers G004, score 90
# ---------------------------------------------------------------------------

def test_advert_blocks_too_close_triggers_g004():
    """Two advert blocks separated by only 3 min → G004, -10, score 90."""
    # 30-min programme; block 1 at 06:02-06:05, gap 3 min, block 2 at 06:08-06:10
    segs = [
        _seg(SegmentType.STATION_ID, "06:00", 2),   # G001 ok
        _seg(SegmentType.ADVERT,     "06:02", 3),   # block 1 ends 06:05
        _seg(SegmentType.TALK,       "06:05", 3),   # gap = 3 min < 10
        _seg(SegmentType.ADVERT,     "06:08", 2),   # block 2 starts 06:08
        _seg(SegmentType.TALK,       "06:10", 8),
        _seg(SegmentType.STATION_ID, "06:18", 2),   # G002 (15-30) ok
        _seg(SegmentType.MUSIC,      "06:20", 10),
    ]
    result = validate_compliance(segs, _prog(duration=30))

    assert "G004" in _rule_ids(result)
    assert result.compliance_score == 90
    assert result.compliance_risk == "compliant"


# ---------------------------------------------------------------------------
# Test 6 — Multiple violations combine penalties correctly
# ---------------------------------------------------------------------------

def test_multiple_violations_combine_penalties():
    """G001 (-10) + G003 (-25) = -35 → score 65, risk 'high'."""
    # 60-min programme; no station ID in first 15 min (G001) + 25% adverts (G003)
    segs = [
        _seg(SegmentType.MUSIC,      "06:00", 20),  # no station ID → G001 triggers
        _seg(SegmentType.STATION_ID, "06:20", 2),   # offset 20 → G002 (15-45) ok
        _seg(SegmentType.ADVERT,     "06:22", 15),  # 15 min = 25% → G003 triggers
        _seg(SegmentType.TALK,       "06:37", 10),
        _seg(SegmentType.STATION_ID, "06:47", 2),   # G002 (45-60) ok
        _seg(SegmentType.MUSIC,      "06:49", 11),
    ]
    result = validate_compliance(segs, _prog(duration=60))

    assert "G001" in _rule_ids(result)
    assert "G003" in _rule_ids(result)
    assert result.compliance_score == 65
    assert result.compliance_risk == "high"


# ---------------------------------------------------------------------------
# Test 7 — compliance_risk is "compliant" when score 90-100
# ---------------------------------------------------------------------------

def test_risk_is_compliant_for_score_90_to_100():
    """Score 90 (G001 triggered, -10) → risk must be 'compliant'."""
    segs = [
        _seg(SegmentType.MUSIC,      "06:00", 10),
        _seg(SegmentType.TALK,       "06:10", 10),
        _seg(SegmentType.STATION_ID, "06:20", 2),
        _seg(SegmentType.MUSIC,      "06:22", 8),
    ]
    result = validate_compliance(segs, _prog(duration=30))

    assert result.compliance_score == 90
    assert result.compliance_risk == "compliant"


# ---------------------------------------------------------------------------
# Test 8 — compliance_risk is "moderate" when score 70-89
# ---------------------------------------------------------------------------

def test_risk_is_moderate_for_score_70_to_89():
    """Score 75 (G003 triggered, -25) → risk must be 'moderate'."""
    segs = [
        _seg(SegmentType.STATION_ID, "06:00", 2),
        _seg(SegmentType.ADVERT,     "06:02", 15),  # 25% of 60 min
        _seg(SegmentType.STATION_ID, "06:17", 5),
        _seg(SegmentType.MUSIC,      "06:22", 25),
        _seg(SegmentType.STATION_ID, "06:47", 2),
        _seg(SegmentType.TALK,       "06:49", 11),
    ]
    result = validate_compliance(segs, _prog(duration=60))

    assert result.compliance_score == 75
    assert result.compliance_risk == "moderate"


# ---------------------------------------------------------------------------
# Test 9 — compliance_risk is "high" when score below 70
# ---------------------------------------------------------------------------

def test_risk_is_high_for_score_below_70():
    """Score 65 (G001 -10 + G003 -25 = -35) → risk must be 'high'."""
    segs = [
        _seg(SegmentType.MUSIC,      "06:00", 20),
        _seg(SegmentType.STATION_ID, "06:20", 2),
        _seg(SegmentType.ADVERT,     "06:22", 15),
        _seg(SegmentType.TALK,       "06:37", 10),
        _seg(SegmentType.STATION_ID, "06:47", 2),
        _seg(SegmentType.MUSIC,      "06:49", 11),
    ]
    result = validate_compliance(segs, _prog(duration=60))

    assert result.compliance_score == 65
    assert result.compliance_risk == "high"


# ---------------------------------------------------------------------------
# Test 10 — G005 triggers when segment types inconsistent with programme type
# ---------------------------------------------------------------------------

def test_g005_triggers_for_inconsistent_programme_type():
    """MUSIC_ONLY programme with TALK segments → G005, -3, score 97."""
    segs = [
        _seg(SegmentType.STATION_ID, "06:00", 2),   # G001 ok
        _seg(SegmentType.MUSIC,      "06:02", 18),
        _seg(SegmentType.STATION_ID, "06:20", 2),   # G002 (15-30) ok
        _seg(SegmentType.TALK,       "06:22", 3),   # TALK forbidden in MUSIC_ONLY
        _seg(SegmentType.MUSIC,      "06:25", 5),
    ]
    result = validate_compliance(
        segs,
        _prog(duration=30, prog_type=ProgrammeType.MUSIC_ONLY),
    )

    assert "G005" in _rule_ids(result)
    assert result.compliance_score == 97
    assert result.compliance_risk == "compliant"
