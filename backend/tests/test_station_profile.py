"""12 tests for Session K6 — station profile statistics that genuinely
drive the recommendations engine and conflict detector.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import date

from app.ai.conflict_detector import detect_conflicts
from app.ai.recommendations.engine import generate_recommendations
from app.ai.recommendations.station_profile import (
    build_station_profile,
)
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

@dataclass
class FakeStat:
    stat_value: str
    notes: str | None = None


@dataclass
class FakeSettings:
    station_audience: str | None = None
    default_region: str | None = None


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
    duration: int = 180,
    broadcast_date: date = date(2026, 5, 20),
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
# Parsing tests (1-4, 12)
# ---------------------------------------------------------------------------

def test_parse_single_peak_window() -> None:
    stats = {"peak_listening_window": FakeStat("06:00-09:00")}
    profile = build_station_profile(stats, None)
    assert profile.peak_windows == [(6 * 60, 9 * 60)]


def test_parse_multiple_peak_windows() -> None:
    stats = {"peak_listening_window": FakeStat("05:30-08:00,17:00-19:00")}
    profile = build_station_profile(stats, None)
    assert profile.peak_windows == [
        (5 * 60 + 30, 8 * 60),
        (17 * 60, 19 * 60),
    ]


def test_parse_window_with_whitespace() -> None:
    stats = {"peak_listening_window": FakeStat("06:00 - 09:00 ; 16:00 - 18:00")}
    profile = build_station_profile(stats, None)
    assert profile.peak_windows == [
        (6 * 60, 9 * 60),
        (16 * 60, 18 * 60),
    ]


def test_invalid_window_string_is_skipped() -> None:
    stats = {"peak_listening_window": FakeStat("not a time, 25:00-26:00, 06:00-09:00, bogus")}
    profile = build_station_profile(stats, None)
    # Only the valid range should survive
    assert profile.peak_windows == [(6 * 60, 9 * 60)]


def test_empty_input_handled_gracefully() -> None:
    profile = build_station_profile(None, None)
    assert profile.peak_windows == []
    assert profile.low_windows == []
    assert profile.audience_size_by_hour == {}
    assert profile.preferred_languages == []
    assert profile.audience_type is None
    assert profile.region is None
    assert profile.has_any_data() is False

    # Also: completely empty dict with no settings
    profile2 = build_station_profile({}, None)
    assert profile2.has_any_data() is False


# ---------------------------------------------------------------------------
# C009 conflict-detector tests (5, 6)
# ---------------------------------------------------------------------------

def test_c009_uses_station_peak_when_provided() -> None:
    # Programme runs 13:00-15:00; station peak is 13:30-14:30; no engagement
    prog = _prog(programme_type=ProgrammeType.MORNING_SHOW,
                 start_time="13:00", duration=120)
    segments = [
        _seg("Intro", SegmentType.INTRO, "13:00", 5),
        _seg("Music", SegmentType.MUSIC, "13:05", 50),
        _seg("Music 2", SegmentType.MUSIC, "13:55", 50),
        _seg("Close", SegmentType.CLOSE, "14:45", 15),
    ]
    stats = {"peak_listening_window": FakeStat("13:30-14:30")}
    profile = build_station_profile(stats, None)

    conflicts = detect_conflicts(segments, prog, station_profile=profile)
    c009 = [c for c in conflicts if c.rule_id == "C009"]
    assert len(c009) == 1
    assert "13:30-14:30" in c009[0].message
    assert "peak listening window" in c009[0].message.lower()


def test_c009_falls_back_to_default_when_no_profile() -> None:
    # Morning show that overlaps 06:30-09:00 with no engagement segments
    prog = _prog(programme_type=ProgrammeType.MORNING_SHOW,
                 start_time="06:00", duration=180)
    segments = [
        _seg("Intro", SegmentType.INTRO, "06:00", 5),
        _seg("Music", SegmentType.MUSIC, "06:05", 55),
        _seg("Music 2", SegmentType.MUSIC, "07:00", 60),
        _seg("Music 3", SegmentType.MUSIC, "08:00", 55),
        _seg("Close", SegmentType.CLOSE, "08:55", 5),
    ]

    # Without profile — should fall back to Accra default window
    conflicts = detect_conflicts(segments, prog)
    c009 = [c for c in conflicts if c.rule_id == "C009"]
    assert len(c009) == 1
    assert "06:30" in c009[0].message and "09:00" in c009[0].message

    # Also test that explicitly empty profile (no peak windows) hits the default
    profile = build_station_profile(None, None)
    conflicts2 = detect_conflicts(segments, prog, station_profile=profile)
    c009b = [c for c in conflicts2 if c.rule_id == "C009"]
    assert len(c009b) == 1
    assert "06:30" in c009b[0].message and "09:00" in c009b[0].message


# ---------------------------------------------------------------------------
# Audience-size weighting tests (7, 8, 9)
# ---------------------------------------------------------------------------

def _morning_show_segments_no_traffic() -> list[Segment]:
    return [
        _seg("Intro", SegmentType.INTRO, "06:00", 5),
        _seg("Music", SegmentType.MUSIC, "06:05", 55),
        _seg("Music 2", SegmentType.MUSIC, "07:00", 55),
        _seg("Music 3", SegmentType.MUSIC, "07:55", 60),
        _seg("Close", SegmentType.CLOSE, "08:55", 5),
    ]


def test_audience_size_weighting_boosts_high_traffic_hour() -> None:
    """Morning programme hours have 5000 listeners; other hours 100.
    The fired recommendations should be boosted relative to baseline."""
    prog = _prog(start_time="06:00", duration=180)
    segments = _morning_show_segments_no_traffic()

    high_audience = {str(h): (5000 if 6 <= h <= 9 else 100) for h in range(24)}
    stats = {
        "audience_size_by_hour": FakeStat(json.dumps(high_audience)),
    }

    baseline_recs = generate_recommendations(segments, prog)
    boosted_recs = generate_recommendations(segments, prog, user_stats=stats)

    # Find a rec present in both lists by recommendation_id to compare scores
    baseline_by_id = {r.recommendation_id: r for r in baseline_recs}
    boosted_by_id = {r.recommendation_id: r for r in boosted_recs}
    common = set(baseline_by_id) & set(boosted_by_id) - {""}
    assert common, "Expected at least one common recommendation_id between runs"
    # At least one boosted rec should have a strictly higher impact_score
    higher = [
        rid for rid in common
        if boosted_by_id[rid].impact_score > baseline_by_id[rid].impact_score
    ]
    assert higher, (
        "Expected audience-size weighting to boost at least one rec impact_score; "
        f"baseline={ {r: baseline_by_id[r].impact_score for r in common} } "
        f"boosted={ {r: boosted_by_id[r].impact_score for r in common} }"
    )


def test_audience_size_weighting_reduces_low_traffic_hour() -> None:
    """Programme hours have 50 listeners; other hours 1000.
    Recommendations should be reduced in impact."""
    prog = _prog(start_time="06:00", duration=180)
    segments = _morning_show_segments_no_traffic()

    low_audience = {str(h): (50 if 6 <= h <= 9 else 1000) for h in range(24)}
    stats = {"audience_size_by_hour": FakeStat(json.dumps(low_audience))}

    baseline_recs = generate_recommendations(segments, prog)
    reduced_recs = generate_recommendations(segments, prog, user_stats=stats)

    baseline_by_id = {r.recommendation_id: r for r in baseline_recs}
    reduced_by_id = {r.recommendation_id: r for r in reduced_recs}
    common = set(baseline_by_id) & set(reduced_by_id) - {""}
    assert common
    lower = [
        rid for rid in common
        if reduced_by_id[rid].impact_score < baseline_by_id[rid].impact_score
    ]
    assert lower, "Expected weighting to lower at least one rec impact_score"


def test_impact_score_stays_within_0_1_after_weighting() -> None:
    prog = _prog(start_time="06:00", duration=180)
    segments = _morning_show_segments_no_traffic()
    extreme = {str(h): (9999 if 6 <= h <= 9 else 1) for h in range(24)}
    stats = {"audience_size_by_hour": FakeStat(json.dumps(extreme))}

    recs = generate_recommendations(segments, prog, user_stats=stats)
    assert recs
    for r in recs:
        assert 0.0 <= r.impact_score <= 1.0, (
            f"impact_score {r.impact_score} out of range for {r.recommendation_id}"
        )


# ---------------------------------------------------------------------------
# Rural audience boost test (10)
# ---------------------------------------------------------------------------

def test_rural_audience_boosts_local_language_recommendation() -> None:
    """A rural-audience profile should boost local-content recommendations
    (e.g. M010) and surface a preferred-languages tip when languages are set."""
    prog = _prog(start_time="06:00", duration=180)
    segments = [
        _seg("Intro", SegmentType.INTRO, "06:00", 5),
        # All non-local-sounding music names — triggers M010
        _seg("Pop Hour", SegmentType.MUSIC, "06:05", 50),
        _seg("Dance Mix", SegmentType.MUSIC, "06:55", 50),
        _seg("Rock Block", SegmentType.MUSIC, "07:45", 70),
        _seg("Close", SegmentType.CLOSE, "08:55", 5),
    ]
    settings = FakeSettings(station_audience="rural", default_region="northern")
    stats = {"preferred_languages": FakeStat("Twi,Ewe,Dagbani")}

    baseline = generate_recommendations(segments, prog)
    boosted = generate_recommendations(
        segments, prog, user_stats=stats, user_settings=settings
    )

    base_m010 = next((r for r in baseline if r.recommendation_id == "M010"), None)
    boost_m010 = next((r for r in boosted if r.recommendation_id == "M010"), None)
    assert base_m010 is not None
    assert boost_m010 is not None
    assert boost_m010.impact_score > base_m010.impact_score

    # And a preferred-languages tip is added
    lang_rec = next((r for r in boosted if r.recommendation_id == "USR-LANG"), None)
    assert lang_rec is not None
    assert "Twi" in lang_rec.message and "Ewe" in lang_rec.message


# ---------------------------------------------------------------------------
# Low-window suppression (11)
# ---------------------------------------------------------------------------

def test_low_window_suppresses_advert_density_warning() -> None:
    """When the user's low-listenership window covers the period where adverts
    cluster, the advert-density warning (D006/PA004/C004) is suppressed."""
    # Music-only programme noon-14:00 with 4 closely-packed adverts → triggers PA004
    # Use MUSIC_ONLY to avoid competing pacing rules eating PA004 in dedup.
    prog = _prog(programme_type=ProgrammeType.MUSIC_ONLY,
                 start_time="12:00", duration=120)
    segments = [
        _seg("Mix 1", SegmentType.MUSIC, "12:00", 10),
        _seg("Ad 1", SegmentType.ADVERT, "12:10", 2),
        _seg("Ad 2", SegmentType.ADVERT, "12:12", 2),
        _seg("Ad 3", SegmentType.ADVERT, "12:14", 2),
        _seg("Ad 4", SegmentType.ADVERT, "12:16", 2),
        _seg("Mix 2", SegmentType.MUSIC, "12:18", 102),
    ]

    # Without profile — PA004 should fire (advert clustering)
    baseline = generate_recommendations(segments, prog)
    baseline_ids = {r.recommendation_id for r in baseline}
    assert "PA004" in baseline_ids, (
        f"Expected PA004 in baseline; got {baseline_ids}"
    )

    # With a low window covering 12:00-14:00 — advert density warning suppressed
    stats = {"low_listening_window": FakeStat("12:00-14:00")}
    suppressed = generate_recommendations(segments, prog, user_stats=stats)
    suppressed_ids = {r.recommendation_id for r in suppressed}
    for rid in {"PA004", "D006", "C004"}:
        assert rid not in suppressed_ids, (
            f"Low-window should have suppressed {rid}; got {suppressed_ids}"
        )
