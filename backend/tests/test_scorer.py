import uuid
from datetime import date

import pytest

from app.ai.scorer import generate_recommendations
from app.ai.scheduling_engine import generate
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

def _seg(
    name: str,
    seg_type: SegmentType,
    start: str,
    duration: int,
) -> Segment:
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
    duration: int = 60,
    preference: TalkMusicPreference = TalkMusicPreference.BALANCED,
) -> ProgrammeInput:
    return ProgrammeInput(
        programme_type=ProgrammeType.MORNING_SHOW,
        station_name="Test FM",
        broadcast_date=date(2026, 5, 11),
        start_time="06:00",
        total_duration_minutes=duration,
        presenter_name="Test Presenter",
        max_advert_blocks_per_hour=3,
        talk_music_preference=preference,
    )


def _engine_result(duration: int = 60) -> tuple[list[Segment], ProgrammeInput]:
    prog = _prog(duration=duration)
    return generate(prog), prog


# ---------------------------------------------------------------------------
# Return-type contracts
# ---------------------------------------------------------------------------

def test_returns_tuple() -> None:
    segs, prog = _engine_result()
    result = generate_recommendations(segs, prog)
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_first_element_is_list_of_recommendations() -> None:
    segs, prog = _engine_result()
    recs, _ = generate_recommendations(segs, prog)
    assert isinstance(recs, list)
    for r in recs:
        assert isinstance(r, Recommendation)


def test_second_element_is_float() -> None:
    segs, prog = _engine_result()
    _, score = generate_recommendations(segs, prog)
    assert isinstance(score, float)


# ---------------------------------------------------------------------------
# Minimum 3 recommendations
# ---------------------------------------------------------------------------

def test_minimum_three_recommendations_engine_output() -> None:
    """Engine-generated run-sheets must always yield >= 3 recommendations."""
    for duration in (15, 30, 60, 120):
        segs, prog = _engine_result(duration=duration)
        recs, _ = generate_recommendations(segs, prog)
        assert len(recs) >= 3, f"Only {len(recs)} recommendations for {duration}-min show"


def test_minimum_three_recommendations_perfect_sheet() -> None:
    """Even a near-perfect run-sheet must return >= 3 recommendations."""
    prog = _prog(duration=15)
    segs = [
        _seg("Intro",      SegmentType.INTRO,      "06:00", 2),
        _seg("Station ID", SegmentType.STATION_ID, "06:02", 2),
        _seg("Music 1",    SegmentType.MUSIC,       "06:04", 4),
        _seg("Talk",       SegmentType.TALK,        "06:08", 4),
        _seg("Advert",     SegmentType.ADVERT,      "06:12", 1),
        _seg("Close",      SegmentType.CLOSE,       "06:13", 2),
    ]
    recs, _ = generate_recommendations(segs, prog)
    assert len(recs) >= 3


# ---------------------------------------------------------------------------
# Composite score bounds
# ---------------------------------------------------------------------------

def test_composite_score_between_zero_and_one() -> None:
    for duration in (15, 30, 60, 120, 240):
        segs, prog = _engine_result(duration=duration)
        _, score = generate_recommendations(segs, prog)
        assert 0.0 <= score <= 1.0, f"Score {score} out of bounds for {duration}-min show"


def test_composite_score_all_same_type_segments() -> None:
    """A run-sheet of only music segments is a degenerate case — score still in [0, 1]."""
    prog = _prog(duration=20)
    segs = [_seg(f"Music {i}", SegmentType.MUSIC, f"06:{i*4:02d}", 4) for i in range(5)]
    _, score = generate_recommendations(segs, prog)
    assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Dimension 1: balance triggers on mismatch
# ---------------------------------------------------------------------------

def test_balance_triggers_heavy_music_preference_with_all_talk() -> None:
    """heavy_music preference targets 65% music; all-talk should trigger balance."""
    prog = _prog(duration=30, preference=TalkMusicPreference.HEAVY_MUSIC)
    segs = [
        _seg("Talk 1", SegmentType.TALK, "06:00", 10),
        _seg("Talk 2", SegmentType.TALK, "06:10", 10),
        _seg("Talk 3", SegmentType.TALK, "06:20", 10),
    ]
    recs, _ = generate_recommendations(segs, prog)
    assert any(r.category == "balance" for r in recs)


def test_balance_does_not_trigger_when_within_5_percent() -> None:
    """balanced preference with 50% music should score 1.0 (no balance trigger)."""
    prog = _prog(duration=20, preference=TalkMusicPreference.BALANCED)
    segs = [
        _seg("Music", SegmentType.MUSIC, "06:00", 10),  # 50% music
        _seg("Talk",  SegmentType.TALK,  "06:10", 10),  # 50% talk
    ]
    recs, _ = generate_recommendations(segs, prog)
    # balance should not be a triggered recommendation (score = 1.0)
    triggered = [r for r in recs if r.category == "balance" and r.impact_score < 0.75]
    assert len(triggered) == 0


def test_balance_triggers_talk_heavy_preference_with_all_music() -> None:
    """talk_heavy preference targets 35% music; all-music triggers balance."""
    prog = _prog(duration=20, preference=TalkMusicPreference.TALK_HEAVY)
    segs = [
        _seg("Music 1", SegmentType.MUSIC, "06:00", 10),
        _seg("Music 2", SegmentType.MUSIC, "06:10", 10),
    ]
    recs, _ = generate_recommendations(segs, prog)
    assert any(r.category == "balance" for r in recs)


# ---------------------------------------------------------------------------
# Dimension 2: advert distribution triggers on uneven spacing
# ---------------------------------------------------------------------------

def test_advert_triggers_uneven_distribution() -> None:
    prog = _prog(duration=60)
    segs = [
        # Three adverts: two very close together, one far away
        _seg("Advert A", SegmentType.ADVERT, "06:02", 3),
        _seg("Advert B", SegmentType.ADVERT, "06:06", 3),  # gap = 4 min
        _seg("Filler",   SegmentType.MUSIC,  "06:09", 40),
        _seg("Advert C", SegmentType.ADVERT, "06:49", 3),  # gap = 43 min
    ]
    recs, _ = generate_recommendations(segs, prog)
    assert any(r.category == "advert" for r in recs)


def test_advert_triggers_single_block() -> None:
    """Only one advert block scores 0.0, which is below the 0.70 threshold."""
    prog = _prog(duration=30)
    segs = [
        _seg("Music",  SegmentType.MUSIC,  "06:00", 27),
        _seg("Advert", SegmentType.ADVERT, "06:27",  3),
    ]
    recs, _ = generate_recommendations(segs, prog)
    assert any(r.category == "advert" for r in recs)


def test_advert_does_not_trigger_even_distribution() -> None:
    """Perfectly even advert spacing scores 1.0, no advert trigger."""
    prog = _prog(duration=60)
    segs = [
        _seg("Music 1",   SegmentType.MUSIC,  "06:00", 19),
        _seg("Advert 1",  SegmentType.ADVERT, "06:19",  2),
        _seg("Music 2",   SegmentType.MUSIC,  "06:21", 19),
        _seg("Advert 2",  SegmentType.ADVERT, "06:40",  2),
        _seg("Music 3",   SegmentType.MUSIC,  "06:42", 18),
    ]
    recs, _ = generate_recommendations(segs, prog)
    triggered = [r for r in recs if r.category == "advert" and r.impact_score < 0.70]
    assert len(triggered) == 0


# ---------------------------------------------------------------------------
# Message and impact_score contracts
# ---------------------------------------------------------------------------

def test_recommendation_messages_are_non_empty() -> None:
    segs, prog = _engine_result()
    recs, _ = generate_recommendations(segs, prog)
    for r in recs:
        assert isinstance(r.message, str)
        assert len(r.message.strip()) > 0


def test_impact_scores_between_zero_and_one() -> None:
    segs, prog = _engine_result()
    recs, _ = generate_recommendations(segs, prog)
    for r in recs:
        assert 0.0 <= r.impact_score <= 1.0, (
            f"impact_score {r.impact_score} out of range for category '{r.category}'"
        )


def test_no_duplicate_categories() -> None:
    """Each category should appear at most once in the returned list."""
    segs, prog = _engine_result()
    recs, _ = generate_recommendations(segs, prog)
    categories = [r.category for r in recs]
    assert len(categories) == len(set(categories))


# ---------------------------------------------------------------------------
# Transition quality
# ---------------------------------------------------------------------------

def test_transition_triggers_long_same_type_run() -> None:
    prog = _prog(duration=20)
    segs = [
        _seg("Music 1", SegmentType.MUSIC, "06:00", 4),
        _seg("Music 2", SegmentType.MUSIC, "06:04", 4),
        _seg("Music 3", SegmentType.MUSIC, "06:08", 4),  # run of 3 → violation
        _seg("Music 4", SegmentType.MUSIC, "06:12", 4),
        _seg("Talk",    SegmentType.TALK,  "06:16", 4),
    ]
    recs, _ = generate_recommendations(segs, prog)
    assert any(r.category == "transition" for r in recs)


def test_transition_does_not_trigger_max_run_of_two() -> None:
    prog = _prog(duration=16)
    segs = [
        _seg("Music 1", SegmentType.MUSIC, "06:00", 4),
        _seg("Music 2", SegmentType.MUSIC, "06:04", 4),  # run of 2 — OK
        _seg("Talk 1",  SegmentType.TALK,  "06:08", 4),
        _seg("Talk 2",  SegmentType.TALK,  "06:12", 4),  # run of 2 — OK
    ]
    recs, _ = generate_recommendations(segs, prog)
    triggered = [r for r in recs if r.category == "transition" and r.impact_score < 0.80]
    assert len(triggered) == 0
