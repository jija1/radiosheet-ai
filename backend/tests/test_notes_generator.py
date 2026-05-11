import uuid
from datetime import date

import pytest

from app.ai.notes_generator import generate_notes
from app.ai.scheduling_engine import generate
from app.api.v1.runsheet.schemas import (
    ProgrammeInput,
    ProgrammeType,
    Segment,
    SegmentType,
    TalkMusicPreference,
)

STATION  = "Test FM"
PRESENTER = "Jane Doe"


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


def _prog() -> ProgrammeInput:
    return ProgrammeInput(
        programme_type=ProgrammeType.MORNING_SHOW,
        station_name=STATION,
        broadcast_date=date(2026, 5, 11),
        start_time="06:00",
        total_duration_minutes=60,
        presenter_name=PRESENTER,
        max_advert_blocks_per_hour=3,
        talk_music_preference=TalkMusicPreference.BALANCED,
    )


def _standard_runsheet() -> list[Segment]:
    """Five-segment run-sheet: INTRO, MUSIC, NEWS, ADVERT, CLOSE."""
    return [
        _seg("Programme Intro", SegmentType.INTRO,  "06:00",  2),
        _seg("Music Set",       SegmentType.MUSIC,  "06:02",  4),
        _seg("News",            SegmentType.NEWS,   "06:06",  5),
        _seg("Advert Break",    SegmentType.ADVERT, "06:11",  3),
        _seg("Programme Close", SegmentType.CLOSE,  "06:14",  2),
    ]


# ---------------------------------------------------------------------------
# Contract: same segment count, non-empty notes
# ---------------------------------------------------------------------------

def test_returns_same_number_of_segments() -> None:
    segs = _standard_runsheet()
    result = generate_notes(segs, _prog())
    assert len(result) == len(segs)


def test_returns_same_number_engine_output() -> None:
    prog = _prog()
    segs = generate(prog)
    result = generate_notes(segs, prog)
    assert len(result) == len(segs)


def test_every_segment_has_non_empty_notes() -> None:
    segs = _standard_runsheet()
    result = generate_notes(segs, _prog())
    for seg in result:
        assert isinstance(seg.presenter_notes, str)
        assert len(seg.presenter_notes.strip()) > 0, (
            f"Empty notes for segment '{seg.name}' ({seg.type})"
        )


def test_every_segment_has_non_empty_notes_engine_output() -> None:
    prog = _prog()
    result = generate_notes(generate(prog), prog)
    for seg in result:
        assert len(seg.presenter_notes.strip()) > 0


def test_empty_input_returns_empty_list() -> None:
    assert generate_notes([], _prog()) == []


# ---------------------------------------------------------------------------
# Position logic
# ---------------------------------------------------------------------------

def test_first_segment_gets_opening_template() -> None:
    segs = _standard_runsheet()
    result = generate_notes(segs, _prog())
    # INTRO opening: "Good day, you're listening to …"
    assert "Good day" in result[0].presenter_notes


def test_last_segment_gets_closing_template() -> None:
    segs = _standard_runsheet()
    result = generate_notes(segs, _prog())
    # CLOSE closing: "Thank you for listening to …"
    assert "Thank you for listening" in result[-1].presenter_notes


def test_middle_segments_get_middle_template() -> None:
    segs = _standard_runsheet()
    result = generate_notes(segs, _prog())
    # Index 1 (MUSIC, middle): "non-stop music"
    assert "non-stop music" in result[1].presenter_notes
    # Index 2 (NEWS, middle): "news update"
    assert "news update" in result[2].presenter_notes
    # Index 3 (ADVERT, middle): "Stay with us"
    assert "Stay with us" in result[3].presenter_notes


def test_single_segment_gets_opening_template() -> None:
    """A lone segment is treated as opening (first check wins)."""
    segs = [_seg("Intro", SegmentType.INTRO, "06:00", 2)]
    result = generate_notes(segs, _prog())
    assert "Good day" in result[0].presenter_notes


def test_two_segments_opening_and_closing_no_middle() -> None:
    segs = [
        _seg("Intro", SegmentType.INTRO, "06:00",  2),
        _seg("Close", SegmentType.CLOSE, "06:02",  2),
    ]
    result = generate_notes(segs, _prog())
    assert "Good day" in result[0].presenter_notes
    assert "Thank you for listening" in result[1].presenter_notes


# ---------------------------------------------------------------------------
# Each type at each position
# ---------------------------------------------------------------------------

def test_music_opening_template() -> None:
    segs = [_seg("Music", SegmentType.MUSIC, "06:00", 4)]
    assert "kicking things off" in generate_notes(segs, _prog())[0].presenter_notes


def test_music_closing_template() -> None:
    segs = [
        _seg("Filler", SegmentType.INTRO,  "06:00", 2),
        _seg("Music",  SegmentType.MUSIC,  "06:02", 4),
    ]
    assert "final music set" in generate_notes(segs, _prog())[1].presenter_notes


def test_news_opening_template() -> None:
    segs = [_seg("News", SegmentType.NEWS, "06:00", 5)]
    assert "up to speed" in generate_notes(segs, _prog())[0].presenter_notes


def test_news_closing_template() -> None:
    segs = [
        _seg("Filler", SegmentType.MUSIC, "06:00", 4),
        _seg("News",   SegmentType.NEWS,  "06:04", 5),
    ]
    assert "news roundup" in generate_notes(segs, _prog())[1].presenter_notes


def test_weather_opening_template() -> None:
    segs = [_seg("Weather", SegmentType.WEATHER, "06:00", 3)]
    assert "check in on today" in generate_notes(segs, _prog())[0].presenter_notes


def test_weather_closing_template() -> None:
    segs = [
        _seg("Filler",  SegmentType.MUSIC,   "06:00", 4),
        _seg("Weather", SegmentType.WEATHER, "06:04", 3),
    ]
    assert "wrap up today" in generate_notes(segs, _prog())[1].presenter_notes


def test_advert_opening_template() -> None:
    segs = [_seg("Advert", SegmentType.ADVERT, "06:00", 3)]
    assert "quick word from our sponsors" in generate_notes(segs, _prog())[0].presenter_notes


def test_advert_closing_template() -> None:
    segs = [
        _seg("Filler", SegmentType.MUSIC,  "06:00", 4),
        _seg("Advert", SegmentType.ADVERT, "06:04", 3),
    ]
    assert "One last message" in generate_notes(segs, _prog())[1].presenter_notes


def test_close_middle_template() -> None:
    segs = [
        _seg("Intro", SegmentType.INTRO, "06:00", 2),
        _seg("Close", SegmentType.CLOSE, "06:02", 2),
        _seg("Music", SegmentType.MUSIC, "06:04", 4),
    ]
    # Index 1 = middle
    assert "That's all from me" in generate_notes(segs, _prog())[1].presenter_notes


# ---------------------------------------------------------------------------
# Generic fallback for unlisted types
# ---------------------------------------------------------------------------

def test_unknown_type_gets_generic_fallback() -> None:
    """STATION_ID and TALK are not in the six-type table → generic note."""
    segs = [
        _seg("Intro",      SegmentType.INTRO,      "06:00", 2),
        _seg("Station ID", SegmentType.STATION_ID, "06:02", 2),
        _seg("Close",      SegmentType.CLOSE,      "06:04", 2),
    ]
    result = generate_notes(segs, _prog())
    sid_note = result[1].presenter_notes
    assert "Station ID" in sid_note
    assert "2 minutes" in sid_note


def test_talk_segment_gets_generic_fallback() -> None:
    segs = [
        _seg("Intro", SegmentType.INTRO, "06:00", 2),
        _seg("Talk",  SegmentType.TALK,  "06:02", 5),
        _seg("Close", SegmentType.CLOSE, "06:07", 2),
    ]
    result = generate_notes(segs, _prog())
    talk_note = result[1].presenter_notes
    assert "Talk" in talk_note
    assert "5 minutes" in talk_note


# ---------------------------------------------------------------------------
# Station name and presenter name interpolation
# ---------------------------------------------------------------------------

def test_station_name_in_intro_notes() -> None:
    segs = [_seg("Intro", SegmentType.INTRO, "06:00", 2)]
    result = generate_notes(segs, _prog())
    assert STATION in result[0].presenter_notes


def test_station_name_in_all_templated_notes() -> None:
    segs = _standard_runsheet()
    result = generate_notes(segs, _prog())
    # All six typed segments should mention the station name
    for seg in result:
        if seg.type not in (SegmentType.STATION_ID, SegmentType.TALK):
            assert STATION in seg.presenter_notes, (
                f"Station name missing from '{seg.name}' ({seg.type}) note: {seg.presenter_notes!r}"
            )


def test_presenter_name_in_intro_opening() -> None:
    segs = [_seg("Intro", SegmentType.INTRO, "06:00", 2)]
    result = generate_notes(segs, _prog())
    assert PRESENTER in result[0].presenter_notes


def test_presenter_name_in_close_closing() -> None:
    segs = [
        _seg("Filler", SegmentType.MUSIC, "06:00", 4),
        _seg("Close",  SegmentType.CLOSE, "06:04", 2),
    ]
    result = generate_notes(segs, _prog())
    assert PRESENTER in result[-1].presenter_notes


def test_duration_interpolated_in_music_middle() -> None:
    segs = [
        _seg("Intro", SegmentType.INTRO, "06:00",  2),
        _seg("Music", SegmentType.MUSIC, "06:02", 7),
        _seg("Close", SegmentType.CLOSE, "06:09",  2),
    ]
    result = generate_notes(segs, _prog())
    assert "7" in result[1].presenter_notes


# ---------------------------------------------------------------------------
# Original segment objects are not mutated
# ---------------------------------------------------------------------------

def test_original_segments_not_mutated() -> None:
    segs = _standard_runsheet()
    original_notes = [s.presenter_notes for s in segs]
    generate_notes(segs, _prog())
    for seg, orig_note in zip(segs, original_notes):
        assert seg.presenter_notes == orig_note
