"""
Recommendation library — 80+ rule-based checks.
Each check is a function (segments, programme_input) → Recommendation | None.
Categories: pacing, engagement, growth, cultural, monetisation, compliance.
(Old scorer categories balance/advert/placement/transition are kept in scorer.py.)
"""
from __future__ import annotations

from app.ai.recommendations.audience_growth import has_engagement_type, local_music_ratio
from app.ai.recommendations.cultural_calendar import get_holiday_for_date
from app.api.v1.runsheet.schemas import (
    ProgrammeInput,
    ProgrammeType,
    Recommendation,
    Segment,
    SegmentType,
)


def _hhmm(t: str) -> int:
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def _rec(
    rec_id: str,
    category: str,
    message: str,
    impact: float,
    source: str,
    confidence: str,
    severity: str,
) -> Recommendation:
    return Recommendation(
        recommendation_id=rec_id,
        category=category,
        message=message,
        impact_score=impact,
        source=source,
        confidence=confidence,
        severity=severity,
        based_on_history=False,
    )


_ENGAGEMENT_TYPES = {SegmentType.VOX_POP, SegmentType.PHONE_IN_SEGMENT, SegmentType.INTERVIEW}

# ═══════════════════════════════════════════════════════════════════════════
# MORNING SHOW  M001–M015
# ═══════════════════════════════════════════════════════════════════════════

def _m001(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MORNING_SHOW or not segs:
        return None
    start = _hhmm(prog.start_time)
    has_w = any(s.type == SegmentType.WEATHER and _hhmm(s.start_time) - start < 15 for s in segs)
    if not has_w:
        return _rec("M001", "pacing",
                    "No weather segment in the first 15 minutes. Morning audiences expect "
                    "weather updates within the first 15 minutes of broadcast.",
                    0.80, "industry best practice", "high", "warning")
    return None


def _m002(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MORNING_SHOW or not segs:
        return None
    prog_start = _hhmm(prog.start_time)
    if prog_start >= 7 * 60:
        return None
    has_news = any(s.type == SegmentType.NEWS and _hhmm(s.start_time) < 7 * 60 for s in segs)
    if not has_news:
        return _rec("M002", "pacing",
                    "No news bulletin before 07:00. Morning audiences expect early news to "
                    "plan their day during the commute preparation window.",
                    0.75, "industry best practice", "high", "warning")
    return None


def _m003(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MORNING_SHOW or not segs:
        return None
    prog_start = _hhmm(prog.start_time)
    prog_end   = prog_start + prog.total_duration_minutes
    w_start, w_end = 6 * 60 + 30, 9 * 60 + 30  # 06:30–09:30
    if prog_end <= w_start or prog_start >= w_end:
        return None
    traffic_types = {SegmentType.NEWS, SegmentType.TALK}
    has_traffic = any(
        s.type in traffic_types and w_start <= _hhmm(s.start_time) < w_end
        for s in segs
    )
    if not has_traffic:
        return _rec("M003", "engagement",
                    "No traffic/news update scheduled during Accra commute peak "
                    "(06:30–09:30). Commuter-focused content in this window significantly "
                    "improves listener retention.",
                    0.70, "Caradise Ghana Traffic Analysis 2026 (peak 6:30–9:30 am)",
                    "high", "warning")
    return None


def _m004(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MORNING_SHOW or not segs:
        return None
    prog_start = _hhmm(prog.start_time)
    cutoff = prog_start + 30
    early_adverts = [s for s in segs if s.type == SegmentType.ADVERT and _hhmm(s.start_time) < cutoff]
    if len(early_adverts) > 1:
        return _rec("M004", "monetisation",
                    f"{len(early_adverts)} advert blocks in the first 30 minutes. Audience is still "
                    "building early in the morning — heavy advertising before 30 minutes risks "
                    "listener drop-off before the core audience has tuned in.",
                    0.60, "industry best practice", "medium", "suggestion")
    return None


def _m005(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MORNING_SHOW or not segs:
        return None
    prog_start = _hhmm(prog.start_time)
    prog_end   = prog_start + prog.total_duration_minutes
    w_start, w_end = 6 * 60 + 30, 8 * 60  # 06:30–08:00
    if prog_end <= w_start or prog_start >= w_end:
        return None
    has_kids = any(
        s.type in {SegmentType.TALK, SegmentType.STORYTELLING, SegmentType.DRAMA}
        and w_start <= _hhmm(s.start_time) < w_end
        for s in segs
    )
    if not has_kids:
        return _rec("M005", "growth",
                    "Educational content for children during the school commute window "
                    "(06:30–08:00) attracts parent listeners. Stations including kids content "
                    "during this window typically see broader family engagement.",
                    0.55, "industry best practice (family co-listening behaviour)", "medium", "suggestion")
    return None


def _m006(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MORNING_SHOW or not segs:
        return None
    has_engagement = has_engagement_type(segs)
    if not has_engagement:
        return _rec("M006", "engagement",
                    "No live caller engagement (interview, vox-pop, phone-in) found. "
                    "Live caller interaction is the highest-retention segment type for "
                    "morning shows on Ghanaian FM radio.",
                    0.70, "industry best practice", "high", "warning")
    return None


def _m007(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MORNING_SHOW or not segs:
        return None
    sponsor_segs = [s for s in segs if s.type == SegmentType.SPONSOR]
    if not sponsor_segs:
        return _rec("M007", "monetisation",
                    "No sponsor segment found. Morning shows command premium sponsorship "
                    "rates — a dedicated sponsor mention segment adds revenue without "
                    "breaking listener flow.",
                    0.50, "industry best practice", "medium", "tip")
    return None


def _m008(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MORNING_SHOW or not segs:
        return None
    intro_segs = [s for s in segs if s.type == SegmentType.INTRO]
    if intro_segs and intro_segs[0].duration_minutes < 2:
        return _rec("M008", "pacing",
                    f"Programme intro is only {intro_segs[0].duration_minutes} minute(s). "
                    "An intro under 90 seconds does not give the presenter enough time to "
                    "establish tone and welcome the audience.",
                    0.55, "industry best practice", "medium", "suggestion")
    return None


def _m009(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MORNING_SHOW or not segs:
        return None
    # Station ID before first content segment
    first_non_mandatory = next(
        (s for s in segs if s.type not in {SegmentType.INTRO, SegmentType.SIG_TUNE}), None
    )
    first_sid = next((s for s in segs if s.type == SegmentType.STATION_ID), None)
    if first_non_mandatory and not first_sid:
        return _rec("M009", "compliance",
                    "No station identification segment found. Station ID should appear "
                    "within the first 15 minutes of every programme.",
                    0.85, "industry best practice", "high", "warning")
    return None


def _m010(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MORNING_SHOW or not segs:
        return None
    music_segs = [s for s in segs if s.type == SegmentType.MUSIC]
    if not music_segs:
        return None
    ratio = local_music_ratio(segs)
    if ratio < 0.30:
        pct = round(ratio * 100)
        return _rec("M010", "growth",
                    f"Only approximately {pct}% of music segments appear to be local/highlife. "
                    "FM radio in Ghana is most trusted when programming uses culturally "
                    "familiar music. Aim for at least 30% local content in the music mix.",
                    0.65,
                    "Antwi-Boateng et al., Cogent Arts & Humanities, 2023",
                    "medium", "suggestion")
    return None


def _m011(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    """Sports recap on Monday mornings."""
    if prog.programme_type != ProgrammeType.MORNING_SHOW or not segs:
        return None
    if prog.broadcast_date.weekday() != 0:  # 0 = Monday
        return None
    has_sports_content = any(
        s.type in {SegmentType.NEWS, SegmentType.TALK} and "sport" in s.name.lower()
        for s in segs
    )
    if not has_sports_content:
        return _rec("M011", "engagement",
                    "Monday morning with no sports recap segment. Weekend match results "
                    "are a high-interest topic for morning commuters on Mondays — a "
                    "2–3 minute sports update boosts engagement significantly.",
                    0.55, "industry best practice", "medium", "suggestion")
    return None


def _m012(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MORNING_SHOW or not segs:
        return None
    weather_segs = [s for s in segs if s.type == SegmentType.WEATHER]
    if len(weather_segs) >= 2:
        return None
    if not weather_segs:
        return None
    first_w_offset = _hhmm(weather_segs[0].start_time) - _hhmm(prog.start_time)
    if first_w_offset + 30 < prog.total_duration_minutes:
        return _rec("M012", "pacing",
                    "Weather updated only once. A second weather update ~30 minutes after "
                    "the first helps late-tuning listeners and reinforces your service value.",
                    0.45, "industry best practice", "low", "tip")
    return None


def _m013(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MORNING_SHOW or not segs:
        return None
    close_segs = [s for s in segs if s.type == SegmentType.CLOSE]
    if not close_segs:
        return None
    # Check if last 10 minutes has a news/summary segment
    prog_end = _hhmm(prog.start_time) + prog.total_duration_minutes
    has_recap = any(
        s.type == SegmentType.NEWS and _hhmm(s.start_time) >= prog_end - 10
        for s in segs
    )
    if not has_recap:
        return _rec("M013", "pacing",
                    "No news headlines recap in the final 10 minutes. A closing news "
                    "summary reinforces service value and gives the audience reason to "
                    "return for the next bulletin.",
                    0.40, "industry best practice", "low", "tip")
    return None


def _m014(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MORNING_SHOW or not segs:
        return None
    # Check if sig_tune is one of the first two segments
    sig_segs = [s for s in segs if s.type == SegmentType.SIG_TUNE]
    if sig_segs:
        first_sig_idx = segs.index(sig_segs[0])
        if first_sig_idx > 2:
            return _rec("M014", "pacing",
                        f"Signature tune placed at segment position {first_sig_idx + 1}. "
                        "Opening signature tune should be among the first two segments to "
                        "establish the programme identity immediately.",
                        0.50, "industry best practice", "medium", "suggestion")
    return None


def _m015(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MORNING_SHOW or not segs:
        return None
    # Check for farewell/handover segment
    close_segs = [s for s in segs if s.type in {SegmentType.CLOSE, SegmentType.TALK}]
    if not close_segs:
        return _rec("M015", "pacing",
                    "No closing or handover segment detected. A clear close helps the "
                    "audience transition to the next programme and maintains brand loyalty.",
                    0.45, "industry best practice", "low", "tip")
    return None


# ═══════════════════════════════════════════════════════════════════════════
# DRIVE TIME  D001–D012
# ═══════════════════════════════════════════════════════════════════════════

def _d001(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.DRIVE_TIME or not segs:
        return None
    for s in segs:
        if s.type == SegmentType.TALK and s.duration_minutes > 5:
            end = _hhmm(s.end_time)
            nearby = any(
                e.type in _ENGAGEMENT_TYPES and 0 <= _hhmm(e.start_time) - end <= 3
                for e in segs
            )
            if not nearby:
                return _rec("D001", "engagement",
                            f"Talk segment '{s.name}' ({s.duration_minutes} min) exceeds 5 minutes "
                            "without an engagement hook. Drive time listeners are approximately 30% "
                            "more likely to switch stations during unbroken talk over 5 minutes.",
                            0.75,
                            "industry best practice (drive time listener retention)",
                            "high", "warning")
    return None


def _d002(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.DRIVE_TIME or not segs:
        return None
    prog_start = _hhmm(prog.start_time)
    prog_end   = prog_start + prog.total_duration_minutes
    w_start, w_end = 16 * 60 + 30, 19 * 60  # 16:30–19:00
    if prog_end <= w_start or prog_start >= w_end:
        return None
    has_traffic = any(
        s.type == SegmentType.NEWS and w_start <= _hhmm(s.start_time) < w_end
        for s in segs
    )
    if not has_traffic:
        return _rec("D002", "pacing",
                    "No traffic/news update in the evening commute peak (16:30–19:00). "
                    "Evening drive listeners expect road and city updates.",
                    0.70, "Caradise Ghana Traffic Analysis 2026 (peak 4:30–7 pm)",
                    "high", "warning")
    return None


def _d003(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.DRIVE_TIME or not segs:
        return None
    music_segs = [s for s in segs if s.type == SegmentType.MUSIC]
    music_total = sum(s.duration_minutes for s in music_segs)
    if prog.total_duration_minutes > 0 and music_total / prog.total_duration_minutes < 0.25:
        return _rec("D003", "pacing",
                    f"Only {round(music_total / prog.total_duration_minutes * 100)}% music in drive time. "
                    "High-energy music anchors the commute experience — aim for at least 25% music.",
                    0.55, "industry best practice", "medium", "suggestion")
    return None


def _d004(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.DRIVE_TIME or not segs:
        return None
    has_sports = any(
        s.type == SegmentType.NEWS and "sport" in s.name.lower()
        for s in segs
    )
    if not has_sports:
        return _rec("D004", "engagement",
                    "No sports update in drive time. Evening commuters are a key sports "
                    "audience — a 2-minute sports summary boosts retention.",
                    0.55, "industry best practice", "medium", "suggestion")
    return None


def _d005(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.DRIVE_TIME or not segs:
        return None
    has_social = any(
        "social" in s.name.lower() or "twitter" in s.name.lower() or "facebook" in s.name.lower()
        for s in segs
    )
    if not has_social:
        return _rec("D005", "growth",
                    "No social media engagement segment. Encouraging listeners to interact "
                    "via social media during drive time builds community and extends reach.",
                    0.45, "industry best practice", "low", "tip")
    return None


def _d006(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.DRIVE_TIME or not segs:
        return None
    prog_start = _hhmm(prog.start_time)
    prog_end   = prog_start + prog.total_duration_minutes
    peak_start, peak_end = 16 * 60, 18 * 60
    if prog_end <= peak_start or prog_start >= peak_end:
        return None
    peak_adverts = [
        s for s in segs
        if s.type == SegmentType.ADVERT and peak_start <= _hhmm(s.start_time) < peak_end
    ]
    peak_advert_mins = sum(s.duration_minutes for s in peak_adverts)
    peak_window = min(peak_end, prog_end) - max(peak_start, prog_start)
    if peak_window > 0 and peak_advert_mins / peak_window > 0.25:
        return _rec("D006", "monetisation",
                    f"Advert density is {round(peak_advert_mins / peak_window * 100)}% during "
                    "commute peak (16:00–18:00). High advert density during peak listening "
                    "risks listener tune-out at the most valuable daypart.",
                    0.65, "industry best practice", "medium", "warning")
    return None


def _d007(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.DRIVE_TIME or not segs:
        return None
    has_business_news = any(
        s.type == SegmentType.NEWS and any(
            kw in s.name.lower() for kw in {"business", "market", "economy", "finance"}
        )
        for s in segs
    )
    if not has_business_news:
        return _rec("D007", "engagement",
                    "No afternoon business/market news segment. Afternoon commuters include "
                    "business listeners — a brief market update builds authority and loyalty.",
                    0.45, "industry best practice", "low", "tip")
    return None


def _d008(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.DRIVE_TIME or not segs:
        return None
    news_segs = [s for s in segs if s.type == SegmentType.NEWS]
    if news_segs:
        last_news = max(news_segs, key=lambda s: _hhmm(s.start_time))
        prog_end = _hhmm(prog.start_time) + prog.total_duration_minutes
        if _hhmm(last_news.start_time) > prog_end - 10:
            return _rec("D008", "pacing",
                        "News bulletin placed very close to the end of the programme. "
                        "Late-running news cuts into the close and handover — schedule "
                        "the final bulletin with at least 10 minutes before programme end.",
                        0.50, "industry best practice", "medium", "suggestion")
    return None


def _d009(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.DRIVE_TIME or not segs:
        return None
    has_farewell = any(s.type in {SegmentType.CLOSE, SegmentType.TALK} for s in segs)
    if not has_farewell:
        return _rec("D009", "pacing",
                    "No farewell or handover segment detected. A clear close with "
                    "next-show teaser retains listeners into the following programme.",
                    0.45, "industry best practice", "low", "tip")
    return None


def _d010(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.DRIVE_TIME or not segs:
        return None
    prog_start = _hhmm(prog.start_time)
    prog_end   = prog_start + prog.total_duration_minutes
    # Expect station ID every 30 min during peak
    station_ids = [s for s in segs if s.type == SegmentType.STATION_ID]
    expected = max(1, prog.total_duration_minutes // 30)
    if len(station_ids) < expected:
        return _rec("D010", "compliance",
                    f"Only {len(station_ids)} station ID(s) for a {prog.total_duration_minutes}-minute "
                    "drive-time programme. Station identification every 30 minutes is standard "
                    "best practice during peak listening.",
                    0.60, "industry best practice", "medium", "suggestion")
    return None


def _d011(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.DRIVE_TIME or not segs:
        return None
    prog_start = _hhmm(prog.start_time)
    phone_in = [s for s in segs if s.type == SegmentType.PHONE_IN_SEGMENT]
    if phone_in:
        early = [s for s in phone_in if _hhmm(s.start_time) - prog_start < 60]
        if early:
            return _rec("D011", "pacing",
                        "Phone-in segment scheduled within first 60 minutes. Drive-time "
                        "phone-ins perform best after 16:00 when the audience has fully built.",
                        0.45, "industry best practice", "low", "tip")
    return None


def _d012(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.DRIVE_TIME or not segs:
        return None
    prog_start = _hhmm(prog.start_time)
    prog_end   = prog_start + prog.total_duration_minutes
    w_start, w_end = 15 * 60 + 30, 17 * 60  # 15:30–17:00
    if prog_end <= w_start or prog_start >= w_end:
        return None
    has_kids = any(
        s.type in {SegmentType.STORYTELLING, SegmentType.DRAMA, SegmentType.TALK}
        and w_start <= _hhmm(s.start_time) < w_end
        for s in segs
    )
    if not has_kids:
        return _rec("D012", "growth",
                    "Adding short educational kids content during school pickup window "
                    "(15:30–17:00) builds parent loyalty. Family-tuned vehicles often "
                    "stay on stations playing kids-friendly content.",
                    0.50, "industry best practice (family co-listening behaviour)", "medium", "tip")
    return None


# ═══════════════════════════════════════════════════════════════════════════
# SPORTS SHOW  S001–S011
# ═══════════════════════════════════════════════════════════════════════════

def _s001(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.SPORTS_SHOW or not segs:
        return None
    for s in segs:
        if s.type == SegmentType.TALK and s.duration_minutes > 4:
            end = _hhmm(s.end_time)
            nearby = any(
                e.type in _ENGAGEMENT_TYPES and 0 <= _hhmm(e.start_time) - end <= 3
                for e in segs
            )
            if not nearby:
                return _rec("S001", "engagement",
                            f"Sports talk '{s.name}' ({s.duration_minutes} min) runs without "
                            "listener engagement (trivia, polls, phone-in). Sports talk over "
                            "4 minutes without an engagement hook shows reduced listener retention.",
                            0.70, "industry best practice (sports talk retention patterns)",
                            "high", "warning")
    return None


def _s002(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.SPORTS_SHOW or not segs:
        return None
    has_score_update = any(
        s.type == SegmentType.NEWS and any(
            kw in s.name.lower() for kw in {"score", "result", "update", "live"}
        )
        for s in segs
    )
    if not has_score_update:
        return _rec("S002", "pacing",
                    "No live score update window detected. Sports audiences tune in for "
                    "real-time updates — a dedicated score window every 20–30 minutes "
                    "anchors the listener.",
                    0.75, "industry best practice", "high", "warning")
    return None


def _s003(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.SPORTS_SHOW or not segs:
        return None
    has_fixtures = any(
        "fixture" in s.name.lower() or "schedule" in s.name.lower() or "upcoming" in s.name.lower()
        for s in segs
    )
    if not has_fixtures:
        return _rec("S003", "engagement",
                    "No fixture announcement segment. Upcoming match schedules give listeners "
                    "reason to tune in again — always include a fixtures preview.",
                    0.55, "industry best practice", "medium", "suggestion")
    return None


def _s004(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.SPORTS_SHOW or not segs:
        return None
    has_expert = any(
        s.type == SegmentType.INTERVIEW or "expert" in s.name.lower() or "analyst" in s.name.lower()
        for s in segs
    )
    if not has_expert:
        return _rec("S004", "growth",
                    "No expert interview or analyst segment. Expert commentary "
                    "significantly elevates the perceived quality of sports programming.",
                    0.60, "industry best practice", "medium", "suggestion")
    return None


def _s005(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.SPORTS_SHOW or not segs:
        return None
    music_total = sum(s.duration_minutes for s in segs if s.type == SegmentType.MUSIC)
    if prog.total_duration_minutes > 0 and music_total / prog.total_duration_minutes > 0.30:
        return _rec("S005", "pacing",
                    f"Music fills {round(music_total / prog.total_duration_minutes * 100)}% of "
                    "the sports show. Sports audiences primarily expect talk, commentary and "
                    "analysis — reduce music to under 30%.",
                    0.65, "industry best practice", "medium", "suggestion")
    return None


def _s006(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.SPORTS_SHOW or not segs:
        return None
    has_phone_in = any(s.type == SegmentType.PHONE_IN_SEGMENT for s in segs)
    if not has_phone_in:
        return _rec("S006", "engagement",
                    "No fan call-in window. Fan phone-ins are the highest-engagement "
                    "format for sports shows — listener opinion drives loyalty and "
                    "social media amplification.",
                    0.70, "industry best practice", "high", "warning")
    return None


def _s007(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.SPORTS_SHOW or not segs:
        return None
    has_local_teams = any(
        "local" in s.name.lower() or "accra" in s.name.lower() or "ghana" in s.name.lower()
        or "kotoko" in s.name.lower() or "hearts" in s.name.lower()
        for s in segs
    )
    if not has_local_teams:
        return _rec("S007", "growth",
                    "No local team coverage detected. Ghanaian sports listeners prioritise "
                    "local club and national team news — include at least one local focus segment.",
                    0.65, "industry best practice", "medium", "suggestion")
    return None


def _s008(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.SPORTS_SHOW or not segs:
        return None
    has_social = any(
        "social" in s.name.lower() or "twitter" in s.name.lower()
        or "whatsapp" in s.name.lower()
        for s in segs
    )
    if not has_social:
        return _rec("S008", "growth",
                    "No social media handle or engagement mention. Sports audiences are highly "
                    "active on social media — regular handle mentions extend programme reach.",
                    0.45, "industry best practice", "low", "tip")
    return None


def _s009(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.SPORTS_SHOW or not segs:
        return None
    advert_segs = [s for s in segs if s.type == SegmentType.ADVERT]
    gambling_adjacent = any(
        any(kw in s.name.lower() for kw in {"bet", "gambling", "odds", "prediction"})
        for s in advert_segs
    )
    if gambling_adjacent:
        return _rec("S009", "compliance",
                    "Potential betting/gambling advert detected. Ensure all betting-related "
                    "advertisements include responsible gambling caveats per NCA guidelines.",
                    0.80, "NCA Ghana Broadcasting Guidelines — responsible broadcasting",
                    "high", "warning")
    return None


def _s010(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.SPORTS_SHOW or not segs:
        return None
    has_recap = any(
        "recap" in s.name.lower() or "review" in s.name.lower() or "highlight" in s.name.lower()
        for s in segs
    )
    if not has_recap:
        return _rec("S010", "pacing",
                    "No match recap or highlights segment. A structured match review "
                    "segment provides the core content hook that sports listeners return for.",
                    0.65, "industry best practice", "medium", "suggestion")
    return None


def _s011(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.SPORTS_SHOW or not segs:
        return None
    has_commentary = any(
        "commentary" in s.name.lower() or "match" in s.name.lower() or "live" in s.name.lower()
        for s in segs
    )
    if not has_commentary and prog.total_duration_minutes >= 60:
        return _rec("S011", "engagement",
                    "No match commentary or live segment for a long-form sports show. "
                    "Live commentary drives the highest concurrent listenership.",
                    0.60, "industry best practice", "medium", "suggestion")
    return None


# ═══════════════════════════════════════════════════════════════════════════
# TALK SHOW  T001–T007
# ═══════════════════════════════════════════════════════════════════════════

def _t001(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.TALK_SHOW or not segs:
        return None
    music_total = sum(s.duration_minutes for s in segs if s.type == SegmentType.MUSIC)
    if prog.total_duration_minutes > 0 and music_total / prog.total_duration_minutes > 0.20:
        return _rec("T001", "pacing",
                    f"Music fills {round(music_total / prog.total_duration_minutes * 100)}% of "
                    "a talk show. Talk show audiences expect less than 20% music — prioritise "
                    "discussion, debate and phone-ins.",
                    0.70, "industry best practice", "high", "warning")
    return None


def _t002(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.TALK_SHOW or not segs:
        return None
    has_phone_in = any(s.type == SegmentType.PHONE_IN_SEGMENT for s in segs)
    if not has_phone_in:
        return _rec("T002", "engagement",
                    "No caller segment in talk show. Caller queue-building from the opening "
                    "and early phone-in windows are essential for talk show audience growth.",
                    0.75, "industry best practice", "high", "warning")
    return None


def _t003(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.TALK_SHOW or not segs:
        return None
    intro_segs = [s for s in segs if s.type == SegmentType.INTRO]
    if intro_segs and intro_segs[0].duration_minutes < 5:
        return _rec("T003", "pacing",
                    f"Topic introduction is only {intro_segs[0].duration_minutes} minutes. "
                    "Talk shows need a minimum 5-minute topic set-up for listeners to "
                    "understand the discussion context before calling in.",
                    0.60, "industry best practice", "medium", "suggestion")
    return None


def _t004(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.TALK_SHOW or not segs:
        return None
    has_guest = any(s.type == SegmentType.INTERVIEW for s in segs)
    if not has_guest:
        return _rec("T004", "engagement",
                    "No expert guest or interview segment. A credible guest elevates the "
                    "discussion and gives listeners reason to tune into the full programme.",
                    0.65, "industry best practice", "medium", "suggestion")
    return None


def _t005(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.TALK_SHOW or not segs:
        return None
    # Check for topic-switch fatigue: many short talk segments suggest topic fragmentation
    short_talks = [s for s in segs if s.type == SegmentType.TALK and s.duration_minutes <= 2]
    if len(short_talks) >= 4:
        return _rec("T005", "pacing",
                    f"{len(short_talks)} talk segments are 2 minutes or shorter. Frequent "
                    "topic switching fragments listener attention — aim for fewer, deeper "
                    "discussion segments of 5+ minutes.",
                    0.55, "industry best practice", "medium", "suggestion")
    return None


def _t006(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.TALK_SHOW or not segs:
        return None
    has_social = any(
        "social" in s.name.lower() or "twitter" in s.name.lower()
        or "whatsapp" in s.name.lower()
        for s in segs
    )
    if not has_social:
        return _rec("T006", "growth",
                    "No social media topic seeding segment. Talk shows that invite social "
                    "engagement early see 2–3× listener interaction and sharing.",
                    0.50, "industry best practice", "medium", "suggestion")
    return None


def _t007(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.TALK_SHOW or not segs:
        return None
    has_summary = any(
        s.type == SegmentType.CLOSE or "summary" in s.name.lower() or "close" in s.name.lower()
        for s in segs
    )
    if not has_summary:
        return _rec("T007", "pacing",
                    "No closing summary segment. A brief summary of discussion conclusions "
                    "and actionable takeaways improves listener satisfaction and recall.",
                    0.45, "industry best practice", "low", "tip")
    return None


# ═══════════════════════════════════════════════════════════════════════════
# RELIGIOUS SHOW  R001–R008
# ═══════════════════════════════════════════════════════════════════════════

def _r001(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.RELIGIOUS_SHOW or not segs:
        return None
    music_segs = [s for s in segs if s.type == SegmentType.MUSIC]
    secular_music = [s for s in music_segs if not any(
        kw in s.name.lower() for kw in {"gospel", "worship", "praise", "hymn", "christian",
                                          "church", "islamic", "devotional"}
    )]
    if secular_music and len(secular_music) > len(music_segs) / 2:
        return _rec("R001", "compliance",
                    f"{len(secular_music)} music segment(s) appear to be secular music in a "
                    "religious programme. Secular pop/dance music is inappropriate for "
                    "religious broadcast slots and may alienate the core audience.",
                    0.80, "industry best practice", "high", "warning")
    return None


def _r002(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.RELIGIOUS_SHOW or not segs:
        return None
    has_scripture = any(
        s.type in {SegmentType.SCRIPTED_REPORT, SegmentType.TALK}
        and any(kw in s.name.lower() for kw in {"scripture", "reading", "verse", "bible",
                                                   "quran", "devotional", "sermon"})
        for s in segs
    )
    if not has_scripture:
        return _rec("R002", "pacing",
                    "No scripture or devotional reading segment found. A scripture reading "
                    "or devotional segment is the core content anchor for religious broadcasting.",
                    0.80, "industry best practice", "high", "warning")
    return None


def _r003(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.RELIGIOUS_SHOW or not segs:
        return None
    worship_segs = [
        s for s in segs
        if s.type == SegmentType.MUSIC and any(
            kw in s.name.lower() for kw in {"worship", "praise", "hymn", "gospel"}
        )
    ]
    worship_total = sum(s.duration_minutes for s in worship_segs)
    if prog.total_duration_minutes >= 30 and worship_total < 10:
        return _rec("R003", "pacing",
                    f"Worship music only {worship_total} minutes for a {prog.total_duration_minutes}-minute "
                    "religious show. At least 10 minutes of worship music helps establish "
                    "the spiritual atmosphere.",
                    0.65, "industry best practice", "medium", "suggestion")
    return None


def _r004(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.RELIGIOUS_SHOW or not segs:
        return None
    has_prayer = any(
        "prayer" in s.name.lower() or "intercession" in s.name.lower()
        for s in segs
    )
    if not has_prayer:
        return _rec("R004", "engagement",
                    "No prayer call or intercession window. A dedicated prayer segment "
                    "drives active listener participation and is expected in religious programming.",
                    0.70, "industry best practice", "high", "warning")
    return None


def _r005(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.RELIGIOUS_SHOW or not segs:
        return None
    has_testimony = any(
        "testimon" in s.name.lower() or "witness" in s.name.lower()
        for s in segs
    )
    if not has_testimony:
        return _rec("R005", "engagement",
                    "No testimonial segment. Listener/community testimonials are powerful "
                    "engagement drivers for religious audiences and build programme loyalty.",
                    0.50, "industry best practice", "medium", "suggestion")
    return None


def _r006(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.RELIGIOUS_SHOW or not segs:
        return None
    advert_segs = [s for s in segs if s.type == SegmentType.ADVERT]
    inappropriate = any(
        any(kw in s.name.lower() for kw in {"alcohol", "beer", "betting", "gambling", "casino"})
        for s in advert_segs
    )
    if inappropriate:
        return _rec("R006", "compliance",
                    "Adverts for alcohol or gambling detected in a religious programme. "
                    "Such advertising is inappropriate for religious broadcast slots and "
                    "will alienate the audience.",
                    0.90, "NCA Ghana Broadcasting Guidelines", "high", "critical")
    return None


def _r007(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.RELIGIOUS_SHOW or not segs:
        return None
    has_benediction = any(
        "benediction" in s.name.lower() or "blessing" in s.name.lower()
        or "close" in s.name.lower() or s.type == SegmentType.CLOSE
        for s in segs
    )
    if not has_benediction:
        return _rec("R007", "pacing",
                    "No closing benediction or blessing segment. A formal close/benediction "
                    "gives the programme a complete, satisfying structure.",
                    0.45, "industry best practice", "low", "tip")
    return None


def _r008(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.RELIGIOUS_SHOW or not segs:
        return None
    if prog.broadcast_date.weekday() == 6:  # Sunday
        prog_start = _hhmm(prog.start_time)
        if prog_start < 6 * 60 or prog_start >= 14 * 60:
            return _rec("R008", "pacing",
                        "Sunday religious programme is outside the primary 06:00–14:00 "
                        "worship window. Most Ghanaian congregations expect religious "
                        "broadcasting during the morning church-going window.",
                        0.55, "industry best practice", "medium", "suggestion")
    return None


# ═══════════════════════════════════════════════════════════════════════════
# FARMER SHOW  F001–F008
# ═══════════════════════════════════════════════════════════════════════════

_FARMER_WINDOWS = [(4 * 60, 7 * 60), (17 * 60, 19 * 60)]


def _f001(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.FARMER_SHOW or not segs:
        return None
    start = _hhmm(prog.start_time)
    in_window = any(lo <= start < hi for lo, hi in _FARMER_WINDOWS)
    if not in_window:
        return _rec("F001", "growth",
                    f"Farmer show starts at {prog.start_time}, outside the ideal windows "
                    "(04:00–07:00 or 17:00–19:00). 60–70% of Tamale metropolis population "
                    "is engaged in farming; these windows match farm labour patterns.",
                    0.75,
                    "Antwi-Boateng et al., Cogent Arts & Humanities, 2023",
                    "high", "warning")
    return None


def _f002(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.FARMER_SHOW or not segs:
        return None
    has_weather = any(s.type == SegmentType.WEATHER for s in segs)
    if not has_weather:
        return _rec("F002", "pacing",
                    "No weather or seasonal information segment. Weather and rainfall "
                    "forecasts are the highest-value content for farming communities.",
                    0.80,
                    "Antwi-Boateng et al., Cogent Arts & Humanities, 2023",
                    "high", "warning")
    return None


def _f003(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.FARMER_SHOW or not segs:
        return None
    has_market = any(
        "market" in s.name.lower() or "price" in s.name.lower() or "commodity" in s.name.lower()
        for s in segs
    )
    if not has_market:
        return _rec("F003", "engagement",
                    "No market price update segment. Commodity prices are critical decision "
                    "support for smallholder farmers — a weekly price update is essential.",
                    0.75, "industry best practice", "high", "warning")
    return None


def _f004(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.FARMER_SHOW or not segs:
        return None
    music_segs = [s for s in segs if s.type == SegmentType.MUSIC]
    if not music_segs:
        return None
    ratio = local_music_ratio(segs)
    if ratio < 0.50:
        return _rec("F004", "growth",
                    f"Only approximately {round(ratio * 100)}% of music appears to be local. "
                    "FM radio is most trusted in rural Ghana when local language content "
                    "dominates. Aim for 50%+ local music in farmer shows.",
                    0.70,
                    "Antwi-Boateng et al., Cogent Arts & Humanities, 2023",
                    "high", "suggestion")
    return None


def _f005(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.FARMER_SHOW or not segs:
        return None
    has_extension = any(
        any(kw in s.name.lower() for kw in {"extension", "agric", "farm", "crop", "planting",
                                               "harvest", "seed", "fertiliser", "pesticide"})
        for s in segs
    )
    if not has_extension:
        return _rec("F005", "engagement",
                    "No agricultural extension content detected. Practical farming advice "
                    "(planting techniques, pest control, soil management) is the core value "
                    "proposition of farmer radio programmes.",
                    0.75, "industry best practice", "high", "warning")
    return None


def _f006(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.FARMER_SHOW or not segs:
        return None
    month = prog.broadcast_date.month
    is_planting = month in {3, 4, 5}
    is_harvest  = month in {9, 10, 11}
    all_names   = " ".join(s.name.lower() for s in segs)
    if is_planting and "plant" not in all_names and "seed" not in all_names:
        return _rec("F006", "pacing",
                    "Planting season content not detected (March–May). Seasonal planting tips "
                    "during this period are the highest-value content for farming audiences.",
                    0.65, "industry best practice", "medium", "suggestion")
    if is_harvest and "harvest" not in all_names:
        return _rec("F006", "pacing",
                    "Harvest season content not detected (Sept–Nov). Post-harvest management "
                    "and storage advice are critical for smallholder farmers in this period.",
                    0.65, "industry best practice", "medium", "suggestion")
    return None


def _f007(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.FARMER_SHOW or not segs:
        return None
    has_qa = any(
        s.type in {SegmentType.PHONE_IN_SEGMENT, SegmentType.VOX_POP}
        or any(kw in s.name.lower() for kw in {"q&a", "question", "call-in", "phone"})
        for s in segs
    )
    if not has_qa:
        return _rec("F007", "engagement",
                    "No farmer Q&A or call-in segment. Peer-to-peer knowledge exchange via "
                    "phone-in is the most trusted information format for rural audiences.",
                    0.70,
                    "Antwi-Boateng et al., Cogent Arts & Humanities, 2023",
                    "high", "warning")
    return None


def _f008(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.FARMER_SHOW or not segs:
        return None
    has_disease_alert = any(
        any(kw in s.name.lower() for kw in {"disease", "blight", "pest", "alert", "warning"})
        for s in segs
    )
    month = prog.broadcast_date.month
    high_risk_months = {4, 5, 6, 10, 11}  # typical wet seasons
    if month in high_risk_months and not has_disease_alert:
        return _rec("F008", "compliance",
                    "No crop disease or pest alert segment during high-risk season. "
                    "Timely disease alerts prevent crop losses for smallholder farmers.",
                    0.60, "industry best practice", "medium", "suggestion")
    return None


# ═══════════════════════════════════════════════════════════════════════════
# NEWS HOUR  N001–N008
# ═══════════════════════════════════════════════════════════════════════════

def _n001(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.NEWS_HOUR or not segs:
        return None
    news_segs = [s for s in segs if s.type == SegmentType.NEWS]
    if news_segs:
        lead = news_segs[0]
        if lead.duration_minutes < 2:
            return _rec("N001", "pacing",
                        f"Lead news story is only {lead.duration_minutes} minute(s). "
                        "A lead story under 90 seconds is insufficient to establish context — "
                        "allow at least 2 minutes for the top story.",
                        0.70, "industry best practice", "high", "warning")
    return None


def _n002(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.NEWS_HOUR or not segs:
        return None
    has_headline = any(
        "headline" in s.name.lower() or "top stories" in s.name.lower()
        for s in segs
    )
    if not has_headline:
        return _rec("N002", "pacing",
                    "No headline preview segment detected. Opening with a 60-second "
                    "headlines summary anchors listeners who tune in mid-programme.",
                    0.65, "industry best practice", "medium", "suggestion")
    return None


def _n003(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.NEWS_HOUR or not segs:
        return None
    has_local = any(
        "local" in s.name.lower() or "accra" in s.name.lower() or "ghana" in s.name.lower()
        or "regional" in s.name.lower()
        for s in segs
    )
    if not has_local:
        return _rec("N003", "engagement",
                    "No local news segment detected. Ghanaian audiences expect local and "
                    "regional news in every bulletin — it is the primary reason listeners "
                    "choose community FM over national broadcasters.",
                    0.80, "industry best practice", "high", "warning")
    return None


def _n004(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.NEWS_HOUR or not segs:
        return None
    has_weather = any(s.type == SegmentType.WEATHER for s in segs)
    if not has_weather:
        return _rec("N004", "pacing",
                    "No weather segment in news hour. Weather is a mandatory element of "
                    "any comprehensive news programme.",
                    0.70, "industry best practice", "high", "warning")
    return None


def _n005(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.NEWS_HOUR or not segs:
        return None
    has_sports = any(
        s.type == SegmentType.NEWS and "sport" in s.name.lower()
        for s in segs
    )
    if not has_sports:
        return _rec("N005", "engagement",
                    "No sports update in news hour. Sports news is the second most-consumed "
                    "category after national news on Ghanaian FM radio.",
                    0.55, "industry best practice", "medium", "suggestion")
    return None


def _n006(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.NEWS_HOUR or not segs:
        return None
    news_segs = [s for s in segs if s.type == SegmentType.NEWS]
    if len(news_segs) >= 3:
        # Check if a high-impact story (breaking) is buried after less important ones
        all_names = [s.name.lower() for s in news_segs]
        politics_first = any("politic" in n or "government" in n or "minister" in n for n in all_names[:1])
        breaking = any("breaking" in n or "urgent" in n for n in all_names[1:])
        if breaking and not politics_first:
            return _rec("N006", "pacing",
                        "A 'breaking' story appears after political news. Lead with the most "
                        "time-sensitive story for maximum audience impact.",
                        0.60, "industry best practice", "medium", "suggestion")
    return None


def _n007(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.NEWS_HOUR or not segs:
        return None
    prog_end = _hhmm(prog.start_time) + prog.total_duration_minutes
    has_closing_headlines = any(
        s.type == SegmentType.NEWS and _hhmm(s.start_time) >= prog_end - 5
        for s in segs
    )
    if not has_closing_headlines:
        return _rec("N007", "pacing",
                    "No closing headlines recap in the final 5 minutes. A brief closing "
                    "headlines summary reinforces key stories and gives the programme a "
                    "professional finish.",
                    0.50, "industry best practice", "medium", "suggestion")
    return None


def _n008(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.NEWS_HOUR or not segs:
        return None
    has_attribution = any(
        "correspond" in s.name.lower() or "reporter" in s.name.lower()
        or "source" in s.name.lower()
        for s in segs
    )
    if not has_attribution:
        return _rec("N008", "compliance",
                    "No source attribution or correspondent segment detected. Transparent "
                    "sourcing is a credibility requirement for news broadcasting.",
                    0.55, "industry best practice", "medium", "suggestion")
    return None


# ═══════════════════════════════════════════════════════════════════════════
# MUSIC ONLY  MU001–MU006
# ═══════════════════════════════════════════════════════════════════════════

def _mu001(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MUSIC_ONLY or not segs:
        return None
    # Check genre variety: if all segments have the same type → low variety
    music_segs = [s for s in segs if s.type == SegmentType.MUSIC]
    if len(music_segs) >= 4:
        unique_keywords: set[str] = set()
        for s in music_segs:
            for kw in {"highlife", "afrobeats", "gospel", "rnb", "pop", "jazz", "soul",
                       "hiplife", "dancehall"}:
                if kw in s.name.lower():
                    unique_keywords.add(kw)
        if len(unique_keywords) <= 1:
            return _rec("MU001", "pacing",
                        "Music genre variety appears very low. A healthy music-only "
                        "programme mixes genres to sustain listener interest across the full duration.",
                        0.55, "industry best practice", "medium", "suggestion")
    return None


def _mu002(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MUSIC_ONLY or not segs:
        return None
    station_ids = [s for s in segs if s.type == SegmentType.STATION_ID]
    expected = max(1, prog.total_duration_minutes // 30)
    if len(station_ids) < expected:
        return _rec("MU002", "compliance",
                    f"Only {len(station_ids)} station ID(s) in a {prog.total_duration_minutes}-minute "
                    "music programme. Station identification every 30 minutes is required "
                    "to maintain licence compliance.",
                    0.70, "industry best practice", "high", "warning")
    return None


def _mu003(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MUSIC_ONLY or not segs:
        return None
    music_segs = [s for s in segs if s.type == SegmentType.MUSIC]
    ratio = local_music_ratio(segs)
    if music_segs and ratio < 0.30:
        return _rec("MU003", "growth",
                    f"Estimated local music content is below 30%. FM radio in Ghana builds "
                    "audience trust through local and culturally familiar music. "
                    "Aim for at least 30% local content.",
                    0.70,
                    "Antwi-Boateng et al., Cogent Arts & Humanities, 2023",
                    "high", "warning")
    return None


def _mu004(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MUSIC_ONLY or not segs:
        return None
    talk_segs = [s for s in segs if s.type == SegmentType.TALK]
    if not talk_segs and prog.total_duration_minutes >= 30:
        return _rec("MU004", "engagement",
                    "No DJ talk-up windows in music-only programme. Brief DJ talk-ups "
                    "build presenter personality and allow station branding between tracks.",
                    0.50, "industry best practice", "medium", "suggestion")
    return None


def _mu005(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MUSIC_ONLY or not segs:
        return None
    # Check for repeated artist (we look for repeated segment names as a proxy)
    music_segs = [s for s in segs if s.type == SegmentType.MUSIC]
    names = [s.name.lower() for s in music_segs]
    seen: dict[str, int] = {}
    for name in names:
        # Use first word as rough artist proxy
        first_word = name.split()[0] if name.split() else name
        if first_word in seen:
            gap = names.index(name) - seen[first_word]
            if gap < 4:
                return _rec("MU005", "pacing",
                            f"Same artist or segment name '{first_word}' appears within "
                            "4 tracks. Repeat artists within 90 minutes reduce variety perception.",
                            0.50, "industry best practice", "medium", "suggestion")
        seen[first_word] = names.index(name)
    return None


def _mu006(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if prog.programme_type != ProgrammeType.MUSIC_ONLY or not segs:
        return None
    advert_segs = [s for s in segs if s.type == SegmentType.ADVERT]
    if not advert_segs and prog.total_duration_minutes >= 30:
        return _rec("MU006", "monetisation",
                    "No advert blocks in music-only programme. Music-only formats support "
                    "regular commercial breaks — typically 2–3 per hour without disrupting flow.",
                    0.45, "industry best practice", "low", "tip")
    return None


# ═══════════════════════════════════════════════════════════════════════════
# PACING — programme-agnostic  PA001–PA008
# ═══════════════════════════════════════════════════════════════════════════

def _pa001(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if not segs:
        return None
    run = 0
    for s in segs:
        if s.type == SegmentType.TALK:
            run += 1
            if run >= 3:
                return _rec("PA001", "pacing",
                            "3 or more consecutive talk segments detected. Breaking up talk "
                            "runs with music or engagement content maintains listener interest.",
                            0.65, "industry best practice", "medium", "suggestion")
        else:
            run = 0
    return None


def _pa002(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if not segs:
        return None
    run = 0
    for s in segs:
        if s.type == SegmentType.MUSIC:
            run += 1
            if run >= 5:
                return _rec("PA002", "pacing",
                            "5 or more consecutive music segments without any talk or "
                            "station content. Long music blocks without breaks risk listener "
                            "disengagement and miss branding opportunities.",
                            0.55, "industry best practice", "medium", "suggestion")
        else:
            run = 0
    return None


def _pa003(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if not segs:
        return None
    advert_segs = [s for s in segs if s.type == SegmentType.ADVERT]
    if advert_segs:
        return None
    if prog.total_duration_minutes >= 20:
        return _rec("PA003", "monetisation",
                    "No advert blocks in the programme. Even a single commercial break "
                    "improves revenue. Consider placing adverts at natural break points.",
                    0.50, "industry best practice", "medium", "suggestion")
    return None


def _pa004(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if not segs:
        return None
    advert_segs = [s for s in segs if s.type == SegmentType.ADVERT]
    if len(advert_segs) >= 4:
        # Check if 3+ adverts appear within 10 minutes
        offsets = sorted(_hhmm(s.start_time) for s in advert_segs)
        for i in range(len(offsets) - 2):
            if offsets[i + 2] - offsets[i] <= 10:
                return _rec("PA004", "pacing",
                            "3+ advert blocks appear within a 10-minute window. Advert "
                            "clustering creates listener fatigue and risks tune-out.",
                            0.70, "industry best practice", "medium", "warning")
    return None


def _pa005(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if not segs:
        return None
    long_segs = [s for s in segs if s.duration_minutes > 15]
    if long_segs:
        longest = max(long_segs, key=lambda s: s.duration_minutes)
        return _rec("PA005", "pacing",
                    f"Segment '{longest.name}' is {longest.duration_minutes} minutes long. "
                    "Segments over 15 minutes without a break risk losing listener attention. "
                    "Consider splitting or inserting a short interlude.",
                    0.60, "industry best practice", "medium", "suggestion")
    return None


def _pa006(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if not segs:
        return None
    if segs[0].type not in {SegmentType.INTRO, SegmentType.SIG_TUNE, SegmentType.STATION_ID}:
        return _rec("PA006", "pacing",
                    f"Programme opens with '{segs[0].name}' ({segs[0].type.value}) rather than "
                    "an intro or signature tune. A cold open without an introductory element "
                    "misses the opportunity to establish programme identity.",
                    0.60, "industry best practice", "medium", "suggestion")
    return None


def _pa007(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if not segs:
        return None
    if segs[-1].type not in {SegmentType.CLOSE, SegmentType.STATION_ID, SegmentType.SIG_TUNE}:
        return _rec("PA007", "pacing",
                    f"Programme closes with '{segs[-1].name}' ({segs[-1].type.value}). "
                    "An abrupt close without a wind-down segment leaves the audience without "
                    "a clear programme ending — always close with a dedicated close segment.",
                    0.55, "industry best practice", "medium", "suggestion")
    return None


def _pa008(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if len(segs) < 2:
        return None
    for i in range(1, len(segs)):
        if segs[i].type == segs[i - 1].type and segs[i].type == SegmentType.ADVERT:
            return _rec("PA008", "pacing",
                        "Adjacent advert segments of the same type detected. Repeated segment "
                        "types immediately following each other reduce flow and listener experience.",
                        0.55, "industry best practice", "medium", "suggestion")
    return None


# ═══════════════════════════════════════════════════════════════════════════
# CULTURAL  CU001
# ═══════════════════════════════════════════════════════════════════════════

def _cu001(segs: list[Segment], prog: ProgrammeInput) -> Recommendation | None:
    if not segs:
        return None
    holiday = get_holiday_for_date(prog.broadcast_date)
    if holiday:
        has_acknowledgement = any(
            s.type in {SegmentType.TALK, SegmentType.DRAMA, SegmentType.SCRIPTED_REPORT}
            and any(kw in s.name.lower() for kw in {
                holiday.lower().split()[0], "celebrat", "holiday", "special", "nation"
            })
            for s in segs
        )
        if not has_acknowledgement:
            return _rec("CU001", "cultural",
                        f"Today is {holiday}. A brief acknowledgement segment celebrates "
                        "the occasion and demonstrates the station's community connection.",
                        0.65, "Ghana public holidays (official government calendar)",
                        "high", "suggestion")
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Master library
# ═══════════════════════════════════════════════════════════════════════════

LIBRARY: list[dict] = [
    # id is used for uniqueness testing
    {"id": "M001",  "fn": _m001},
    {"id": "M002",  "fn": _m002},
    {"id": "M003",  "fn": _m003},
    {"id": "M004",  "fn": _m004},
    {"id": "M005",  "fn": _m005},
    {"id": "M006",  "fn": _m006},
    {"id": "M007",  "fn": _m007},
    {"id": "M008",  "fn": _m008},
    {"id": "M009",  "fn": _m009},
    {"id": "M010",  "fn": _m010},
    {"id": "M011",  "fn": _m011},
    {"id": "M012",  "fn": _m012},
    {"id": "M013",  "fn": _m013},
    {"id": "M014",  "fn": _m014},
    {"id": "M015",  "fn": _m015},
    {"id": "D001",  "fn": _d001},
    {"id": "D002",  "fn": _d002},
    {"id": "D003",  "fn": _d003},
    {"id": "D004",  "fn": _d004},
    {"id": "D005",  "fn": _d005},
    {"id": "D006",  "fn": _d006},
    {"id": "D007",  "fn": _d007},
    {"id": "D008",  "fn": _d008},
    {"id": "D009",  "fn": _d009},
    {"id": "D010",  "fn": _d010},
    {"id": "D011",  "fn": _d011},
    {"id": "D012",  "fn": _d012},
    {"id": "S001",  "fn": _s001},
    {"id": "S002",  "fn": _s002},
    {"id": "S003",  "fn": _s003},
    {"id": "S004",  "fn": _s004},
    {"id": "S005",  "fn": _s005},
    {"id": "S006",  "fn": _s006},
    {"id": "S007",  "fn": _s007},
    {"id": "S008",  "fn": _s008},
    {"id": "S009",  "fn": _s009},
    {"id": "S010",  "fn": _s010},
    {"id": "S011",  "fn": _s011},
    {"id": "T001",  "fn": _t001},
    {"id": "T002",  "fn": _t002},
    {"id": "T003",  "fn": _t003},
    {"id": "T004",  "fn": _t004},
    {"id": "T005",  "fn": _t005},
    {"id": "T006",  "fn": _t006},
    {"id": "T007",  "fn": _t007},
    {"id": "R001",  "fn": _r001},
    {"id": "R002",  "fn": _r002},
    {"id": "R003",  "fn": _r003},
    {"id": "R004",  "fn": _r004},
    {"id": "R005",  "fn": _r005},
    {"id": "R006",  "fn": _r006},
    {"id": "R007",  "fn": _r007},
    {"id": "R008",  "fn": _r008},
    {"id": "F001",  "fn": _f001},
    {"id": "F002",  "fn": _f002},
    {"id": "F003",  "fn": _f003},
    {"id": "F004",  "fn": _f004},
    {"id": "F005",  "fn": _f005},
    {"id": "F006",  "fn": _f006},
    {"id": "F007",  "fn": _f007},
    {"id": "F008",  "fn": _f008},
    {"id": "N001",  "fn": _n001},
    {"id": "N002",  "fn": _n002},
    {"id": "N003",  "fn": _n003},
    {"id": "N004",  "fn": _n004},
    {"id": "N005",  "fn": _n005},
    {"id": "N006",  "fn": _n006},
    {"id": "N007",  "fn": _n007},
    {"id": "N008",  "fn": _n008},
    {"id": "MU001", "fn": _mu001},
    {"id": "MU002", "fn": _mu002},
    {"id": "MU003", "fn": _mu003},
    {"id": "MU004", "fn": _mu004},
    {"id": "MU005", "fn": _mu005},
    {"id": "MU006", "fn": _mu006},
    {"id": "PA001", "fn": _pa001},
    {"id": "PA002", "fn": _pa002},
    {"id": "PA003", "fn": _pa003},
    {"id": "PA004", "fn": _pa004},
    {"id": "PA005", "fn": _pa005},
    {"id": "PA006", "fn": _pa006},
    {"id": "PA007", "fn": _pa007},
    {"id": "PA008", "fn": _pa008},
    {"id": "CU001", "fn": _cu001},
]
