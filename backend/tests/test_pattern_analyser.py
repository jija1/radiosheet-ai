"""10 tests for the personal pattern analyser (Session K3)."""
from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ai.pattern_analyser import analyse_patterns
from app.api.v1.runsheet.models import RunSheetRecord
from app.api.v1.runsheet.schemas import (
    ProgrammeInput,
    ProgrammeType,
    RunSheetResponse,
    RunSheetStats,
    Segment,
    SegmentType,
    TalkMusicPreference,
)
from app.db.session import Base
from app.models.audit_log import AuditLog  # noqa: F401 — register table
from app.models.user import User
from app.models.user_statistics import UserStatistic  # noqa: F401 — register table


USER_ID = "user-001"


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    user = User(
        id=USER_ID,
        email="t@example.com",
        hashed_password="x",
        created_at="2026-01-01T00:00:00+00:00",
    )
    session.add(user)
    session.commit()
    try:
        yield session
    finally:
        session.close()


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
    broadcast_date: date = date(2026, 5, 20),
    start_time: str = "06:00",
    duration: int = 60,
    talk_music: TalkMusicPreference = TalkMusicPreference.BALANCED,
) -> ProgrammeInput:
    return ProgrammeInput(
        programme_type=programme_type,
        station_name="History FM",
        broadcast_date=broadcast_date,
        start_time=start_time,
        total_duration_minutes=duration,
        presenter_name="Test Presenter",
        max_advert_blocks_per_hour=3,
        talk_music_preference=talk_music,
    )


def _response(
    segments: list[Segment],
    programme: ProgrammeInput,
    score: float = 0.8,
) -> RunSheetResponse:
    return RunSheetResponse(
        runsheet_id=str(uuid.uuid4()),
        programme_input=programme,
        segments=segments,
        conflicts=[],
        recommendations=[],
        compliance_score=100,
        compliance_risk="compliant",
        compliance_violations=[],
        stats=RunSheetStats(
            total_segments=len(segments),
            total_duration_minutes=programme.total_duration_minutes,
            music_percentage=0.0,
            talk_percentage=0.0,
            advert_percentage=0.0,
            conflict_count=0,
            score=score,
        ),
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def _save_record(
    session,
    segments: list[Segment],
    programme: ProgrammeInput,
    score: float,
    generated_at: datetime,
    user_id: str = USER_ID,
) -> RunSheetRecord:
    stats = RunSheetStats(
        total_segments=len(segments),
        total_duration_minutes=programme.total_duration_minutes,
        music_percentage=0.0,
        talk_percentage=0.0,
        advert_percentage=0.0,
        conflict_count=0,
        score=score,
    )
    record = RunSheetRecord(
        id=str(uuid.uuid4()),
        user_id=user_id,
        programme_type=programme.programme_type.value,
        station_name=programme.station_name,
        presenter_name=programme.presenter_name,
        total_duration_minutes=programme.total_duration_minutes,
        segments_json=json.dumps([s.model_dump(mode="json") for s in segments]),
        conflicts_json=json.dumps([]),
        recommendations_json=json.dumps([]),
        stats_json=json.dumps(stats.model_dump(mode="json")),
        programme_input_json=json.dumps(programme.model_dump(mode="json")),
        generated_at=generated_at.isoformat(),
    )
    session.add(record)
    session.commit()
    return record


def _populate(
    session,
    count: int,
    *,
    segments_factory=None,
    programme_factory=None,
    score: float = 0.8,
    base_date: datetime | None = None,
):
    base_date = base_date or datetime(2026, 5, 1, 6, 0, tzinfo=timezone.utc)
    for i in range(count):
        prog = (programme_factory(i) if programme_factory else _prog())
        segs = (segments_factory(i) if segments_factory else [
            _seg("Intro", SegmentType.INTRO, prog.start_time, 5),
        ])
        _save_record(session, segs, prog, score, base_date + timedelta(days=i))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_returns_empty_list_with_fewer_than_5_runsheets(db_session) -> None:
    _populate(db_session, 4)
    current = _response([_seg("Intro", SegmentType.INTRO, "06:00", 5)], _prog())
    assert analyse_patterns(USER_ID, db_session, current) == []


def test_p001_fires_when_news_deviates_more_than_10_minutes(db_session) -> None:
    def segs(_):
        return [
            _seg("Intro", SegmentType.INTRO, "06:00", 5),
            _seg("News",  SegmentType.NEWS,  "06:10", 5),  # min 10
            _seg("Music", SegmentType.MUSIC, "06:15", 30),
        ]
    _populate(db_session, 5, segments_factory=segs)

    current_segs = [
        _seg("Intro", SegmentType.INTRO, "06:00", 5),
        _seg("News",  SegmentType.NEWS,  "06:25", 5),     # min 25 — deviates 15
        _seg("Music", SegmentType.MUSIC, "06:30", 30),
    ]
    current = _response(current_segs, _prog())
    recs = analyse_patterns(USER_ID, db_session, current)
    assert any(r.recommendation_id == "P001" for r in recs)


def test_p001_does_not_fire_when_news_within_10_minutes_of_typical(db_session) -> None:
    def segs(_):
        return [
            _seg("Intro", SegmentType.INTRO, "06:00", 5),
            _seg("News",  SegmentType.NEWS,  "06:10", 5),
            _seg("Music", SegmentType.MUSIC, "06:15", 30),
        ]
    _populate(db_session, 5, segments_factory=segs)

    current_segs = [
        _seg("Intro", SegmentType.INTRO, "06:00", 5),
        _seg("News",  SegmentType.NEWS,  "06:15", 5),     # min 15 — within 10
        _seg("Music", SegmentType.MUSIC, "06:20", 30),
    ]
    current = _response(current_segs, _prog())
    recs = analyse_patterns(USER_ID, db_session, current)
    assert not any(r.recommendation_id == "P001" for r in recs)


def test_p002_fires_when_first_advert_8_minutes_earlier_than_typical(db_session) -> None:
    def segs(_):
        return [
            _seg("Intro", SegmentType.INTRO, "06:00", 5),
            _seg("Music", SegmentType.MUSIC, "06:05", 15),
            _seg("Advert", SegmentType.ADVERT, "06:20", 3),   # minute 20
            _seg("Talk",  SegmentType.TALK,  "06:23", 20),
        ]
    _populate(db_session, 5, segments_factory=segs)

    current_segs = [
        _seg("Intro",  SegmentType.INTRO,  "06:00", 5),
        _seg("Advert", SegmentType.ADVERT, "06:08", 3),       # minute 8 — 12 earlier
        _seg("Music",  SegmentType.MUSIC,  "06:11", 30),
    ]
    current = _response(current_segs, _prog())
    recs = analyse_patterns(USER_ID, db_session, current)
    assert any(r.recommendation_id == "P002" for r in recs)


def test_p003_fires_when_talk_segment_2x_historical_average(db_session) -> None:
    # historical average talk = 5 min
    def segs(_):
        return [
            _seg("Intro", SegmentType.INTRO, "06:00", 5),
            _seg("Talk1", SegmentType.TALK,  "06:05", 5),
            _seg("Music", SegmentType.MUSIC, "06:10", 30),
        ]
    _populate(db_session, 5, segments_factory=segs)

    current_segs = [
        _seg("Intro", SegmentType.INTRO, "06:00", 5),
        _seg("BigTalk", SegmentType.TALK,  "06:05", 20),  # 4x average
        _seg("Music", SegmentType.MUSIC, "06:25", 20),
    ]
    current = _response(current_segs, _prog())
    recs = analyse_patterns(USER_ID, db_session, current)
    assert any(r.recommendation_id == "P003" for r in recs)


def test_p004_fires_when_recent_average_15_points_below_overall(db_session) -> None:
    base = datetime(2026, 5, 1, 6, 0, tzinfo=timezone.utc)
    # Older 15 records at 95%, recent 5 at 60%
    for i in range(15):
        _save_record(db_session, [_seg("Intro", SegmentType.INTRO, "06:00", 5)],
                     _prog(), 0.95, base + timedelta(days=i))
    for i in range(15, 20):
        _save_record(db_session, [_seg("Intro", SegmentType.INTRO, "06:00", 5)],
                     _prog(), 0.60, base + timedelta(days=i))

    current = _response([_seg("Intro", SegmentType.INTRO, "06:00", 5)], _prog())
    recs = analyse_patterns(USER_ID, db_session, current)
    assert any(r.recommendation_id == "P004" for r in recs)


def test_p005_fires_when_high_scoring_segment_type_missing(db_session) -> None:
    # 5 high-scoring records each containing NEWS
    def segs(_):
        return [
            _seg("Intro", SegmentType.INTRO, "06:00", 5),
            _seg("News",  SegmentType.NEWS,  "06:05", 5),
            _seg("Music", SegmentType.MUSIC, "06:10", 30),
        ]
    _populate(db_session, 5, segments_factory=segs, score=0.95)

    # Current has NO news
    current_segs = [
        _seg("Intro", SegmentType.INTRO, "06:00", 5),
        _seg("Music", SegmentType.MUSIC, "06:05", 30),
    ]
    current = _response(current_segs, _prog())
    recs = analyse_patterns(USER_ID, db_session, current)
    assert any(r.recommendation_id == "P005" for r in recs)


def test_p008_fires_when_5plus_runsheets_and_no_defaults_set(db_session) -> None:
    # User has no default_* preferences set (fixture creates bare user)
    _populate(db_session, 5)
    current = _response([_seg("Intro", SegmentType.INTRO, "06:00", 5)], _prog())
    recs = analyse_patterns(USER_ID, db_session, current)
    assert any(r.recommendation_id == "P008" for r in recs)


def test_all_pattern_recommendations_have_based_on_history_true(db_session) -> None:
    """Populate enough variance so multiple checks fire; every result must
    carry based_on_history=True."""
    base = datetime(2026, 5, 1, 6, 0, tzinfo=timezone.utc)
    # 10 historical records — talk average ≈ 5 min, news at minute 10
    for i in range(10):
        segs = [
            _seg("Intro", SegmentType.INTRO, "06:00", 5),
            _seg("Talk",  SegmentType.TALK,  "06:05", 5),
            _seg("News",  SegmentType.NEWS,  "06:10", 5),
            _seg("Advert",SegmentType.ADVERT,"06:15", 3),
            _seg("Music", SegmentType.MUSIC, "06:18", 30),
        ]
        _save_record(db_session, segs, _prog(), 0.92, base + timedelta(days=i))

    # Current deliberately violates: huge talk, late news, no advert
    current_segs = [
        _seg("Intro",   SegmentType.INTRO, "06:00", 5),
        _seg("BigTalk", SegmentType.TALK,  "06:05", 25),
        _seg("News",    SegmentType.NEWS,  "06:35", 5),
        _seg("Music",   SegmentType.MUSIC, "06:40", 20),
    ]
    current = _response(current_segs, _prog())
    recs = analyse_patterns(USER_ID, db_session, current)
    assert len(recs) >= 1
    for r in recs:
        assert r.based_on_history is True, f"{r.recommendation_id} missing based_on_history"


def test_confidence_high_for_10_plus_medium_for_5_to_9(db_session) -> None:
    # First check medium (5 records)
    _populate(db_session, 5)
    current = _response([_seg("Intro", SegmentType.INTRO, "06:00", 5)], _prog())
    recs = analyse_patterns(USER_ID, db_session, current)
    assert recs, "Expected at least one pattern recommendation (P008)"
    assert all(r.confidence == "medium" for r in recs)

    # Add 5 more for total of 10 → confidence should become high
    base = datetime(2026, 6, 1, 6, 0, tzinfo=timezone.utc)
    for i in range(5):
        _save_record(db_session, [_seg("Intro", SegmentType.INTRO, "06:00", 5)],
                     _prog(), 0.8, base + timedelta(days=i))
    recs = analyse_patterns(USER_ID, db_session, current)
    assert recs
    assert all(r.confidence == "high" for r in recs)
