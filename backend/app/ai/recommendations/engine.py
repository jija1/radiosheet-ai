"""
New recommendations engine — rule-based, context-aware, no forced minimum.
Produces recommendations with source, confidence, severity, and based_on_history fields.
Categories used: pacing, engagement, growth, cultural, monetisation, compliance,
                 station_insight, custom.
(Old scorer categories: balance, advert, placement, transition — kept in scorer.py.)
"""
from __future__ import annotations

from typing import Any

from app.ai.recommendations.library import LIBRARY
from app.ai.recommendations.mood_advisor import get_mood_advice
from app.ai.recommendations.station_profile import (
    StationProfile,
    all_window_labels,
    build_station_profile,
    overlaps,
)
from app.api.v1.runsheet.schemas import (
    ProgrammeInput,
    ProgrammeType,
    Recommendation,
    Segment,
    SegmentType,
)

_SEVERITY_ORDER = {"critical": 0, "warning": 1, "suggestion": 2, "tip": 3}

# Rec IDs whose default windows are replaced by station peak when provided
_PEAK_OVERRIDE_IDS = {"M003", "D002", "D006"}

# Advert-density recs that may be suppressed when overlapping a low window
_ADVERT_DENSITY_IDS = {"C004", "D006", "PA004"}

# Local-language / rural-content boost candidates
_RURAL_BOOST_IDS = {"M010", "MU003", "F004", "F002", "F003", "F005", "F007"}

# Urban boost candidates
_URBAN_BOOST_IDS = {"D003", "D005", "D006", "S008", "T006"}


def generate_recommendations(
    segments: list[Segment],
    programme_input: ProgrammeInput,
    user_stats: dict[str, Any] | None = None,
    deep_dive: bool = False,
    station_profile: StationProfile | None = None,
    user_settings: Any | None = None,
) -> list[Recommendation]:
    """
    Run every library check. Return deduplicated recommendations sorted by
    severity (critical first) then impact_score descending.
    No minimum count enforced — empty list is valid.

    user_stats: optional dict mapping stat_key -> UserStatistic-like object
                (must have .stat_value attribute). When provided,
                local_cultural_note and peak_listening_window are surfaced as
                tip recommendations; custom_recommendation is always appended.

    station_profile: optional structured profile. When omitted, it is built
                     from user_stats + user_settings.

    deep_dive: when True, also append a mood-advisor tip for the broadcast
               start time.
    """
    profile = station_profile
    if profile is None:
        profile = build_station_profile(user_stats, user_settings)

    library_fired: list[Recommendation] = []
    for entry in LIBRARY:
        rec = entry["fn"](segments, programme_input)
        if rec is not None:
            library_fired.append(rec)

    custom_recs: list[Recommendation] = []
    if user_stats:
        peak = _get_value(user_stats, "peak_listening_window")
        if peak:
            library_fired.append(Recommendation(
                category="station_insight",
                message=(
                    f"Station-specific peak listening window applied: {peak}. "
                    "Programming has been evaluated against your station's "
                    "audience window rather than the default commute peaks."
                ),
                impact_score=0.55,
                source="user station statistics",
                confidence="user-provided",
                severity="tip",
                based_on_history=True,
                recommendation_id="USR-PEAK",
            ))

        note = _get_value(user_stats, "local_cultural_note")
        if note:
            library_fired.append(Recommendation(
                category="cultural",
                message=f"Station note: {note}",
                impact_score=0.6,
                source="user station statistics",
                confidence="user-provided",
                severity="tip",
                based_on_history=True,
                recommendation_id="USR-CULTURAL",
            ))

        custom = _get_value(user_stats, "custom_recommendation")
        if custom:
            custom_recs.append(Recommendation(
                category="custom",
                message=custom,
                impact_score=0.5,
                source="user-defined recommendation",
                confidence="user-provided",
                severity="tip",
                based_on_history=True,
                recommendation_id="USR-CUSTOM",
            ))

    if deep_dive:
        try:
            day = programme_input.broadcast_date.weekday()
            advice = get_mood_advice(programme_input.start_time, day)
            mood_msg = (
                f"Mood advisor: at {programme_input.start_time}, energy level is "
                f"'{advice['energy_level']}'. {advice['notes']} "
                f"Suggested genres: {', '.join(advice['preferred_genres'])}."
            )
            library_fired.append(Recommendation(
                category="mood",
                message=mood_msg,
                impact_score=0.45,
                source="time-of-day mood advisor",
                confidence="medium",
                severity="tip",
                recommendation_id="DD-MOOD",
            ))
        except Exception:
            pass

    if profile and profile.has_any_data():
        library_fired = _apply_station_profile(
            library_fired, profile, segments, programme_input
        )

    # Deduplicate by category: keep highest impact_score per category
    best: dict[str, Recommendation] = {}
    for rec in library_fired:
        if rec.category not in best or rec.impact_score > best[rec.category].impact_score:
            best[rec.category] = rec

    deduped = list(best.values()) + custom_recs
    deduped.sort(
        key=lambda r: (_SEVERITY_ORDER.get(r.severity, 99), -r.impact_score)
    )
    return deduped


# ───────────────────────────────────────────────────────────────────────────
# Station-profile post-processing
# ───────────────────────────────────────────────────────────────────────────

def _apply_station_profile(
    recs: list[Recommendation],
    profile: StationProfile,
    segments: list[Segment],
    programme_input: ProgrammeInput,
) -> list[Recommendation]:
    """Apply peak override, audience weighting, low-window suppression,
    and audience-type boosts. Returns a new list."""
    out: list[Recommendation] = []

    prog_start_min = _hhmm(programme_input.start_time)
    prog_end_min = prog_start_min + programme_input.total_duration_minutes

    advert_min_offsets = [
        _hhmm(s.start_time) for s in segments if s.type == SegmentType.ADVERT
    ]

    # Audience size weighting reference values
    audience_weight = _audience_weight_for_programme(profile, prog_start_min, prog_end_min)
    audience_label = _audience_label(profile, prog_start_min, prog_end_min)

    for rec in recs:
        rec_id = rec.recommendation_id

        # 1. Peak window override: rewrite message to use station's actual peak
        if profile.peak_windows and rec_id in _PEAK_OVERRIDE_IDS:
            rec = _rewrite_with_station_peak(rec, profile)

        # 2. Low-window suppression: drop advert-density warnings during low
        if (
            profile.low_windows
            and rec_id in _ADVERT_DENSITY_IDS
            and _adverts_mostly_in_low_window(advert_min_offsets, profile.low_windows)
        ):
            continue

        # 3. Audience size weighting
        if profile.audience_size_by_hour and audience_weight is not None:
            rec = _weight_by_audience(rec, audience_weight, audience_label)

        # 4. Rural / urban boosts
        if profile.is_rural() and rec_id in _RURAL_BOOST_IDS:
            rec = _boost_rec(rec, 1.3, profile, kind="rural")
        elif profile.is_urban() and rec_id in _URBAN_BOOST_IDS:
            rec = _boost_rec(rec, 1.2, profile, kind="urban")

        out.append(rec)

    # 5. Add audience-type and language insight if not yet covered
    extras = _audience_profile_recs(profile, segments, programme_input)
    out.extend(extras)

    # 6. Add low-window aware tip if heavy content sits in a low window
    low_tip = _low_window_content_tip(profile, segments)
    if low_tip is not None:
        out.append(low_tip)

    return out


def _rewrite_with_station_peak(
    rec: Recommendation, profile: StationProfile
) -> Recommendation:
    label = all_window_labels(profile.peak_windows)
    new_msg = (
        f"Your station's peak listening window ({label}) is the active reference. "
        f"{rec.message}"
    )
    return rec.model_copy(update={
        "message": new_msg,
        "source": "user-provided station statistics",
        "confidence": "user-provided",
    })


def _adverts_mostly_in_low_window(
    advert_offsets: list[int], low_windows: list[tuple[int, int]]
) -> bool:
    if not advert_offsets or not low_windows:
        return False
    in_low = sum(
        1 for off in advert_offsets
        if any(lo <= off < hi for lo, hi in low_windows)
    )
    return in_low * 2 >= len(advert_offsets)


def _audience_weight_for_programme(
    profile: StationProfile, prog_start_min: int, prog_end_min: int
) -> float | None:
    counts = profile.audience_size_by_hour
    if not counts:
        return None

    hours: list[int] = []
    h = prog_start_min // 60
    while h * 60 < prog_end_min:
        hours.append(h % 24)
        h += 1
    if not hours:
        return None

    relevant = [counts[hr] for hr in hours if hr in counts]
    if not relevant:
        return None

    mean_overall = sum(counts.values()) / len(counts)
    if mean_overall <= 0:
        return None

    prog_mean = sum(relevant) / len(relevant)
    weight = prog_mean / mean_overall
    return max(0.6, min(1.5, weight))


def _audience_label(
    profile: StationProfile, prog_start_min: int, prog_end_min: int
) -> str | None:
    counts = profile.audience_size_by_hour
    if not counts:
        return None
    hours = []
    h = prog_start_min // 60
    while h * 60 < prog_end_min:
        hours.append(h % 24)
        h += 1
    relevant = [counts[hr] for hr in hours if hr in counts]
    if not relevant:
        return None
    return f"~{max(relevant)} listeners"


def _weight_by_audience(
    rec: Recommendation, weight: float, audience_label: str | None
) -> Recommendation:
    new_impact = rec.impact_score * weight
    new_impact = max(0.0, min(1.0, new_impact))
    msg = rec.message
    if audience_label and weight >= 1.3:
        msg = msg + f" (affects your highest-traffic hour — {audience_label})"
    elif weight <= 0.7:
        msg = msg + " (occurs during a lower-audience hour for your station)"
    return rec.model_copy(update={"message": msg, "impact_score": round(new_impact, 4)})


def _boost_rec(
    rec: Recommendation, factor: float, profile: StationProfile, kind: str
) -> Recommendation:
    new_impact = max(0.0, min(1.0, rec.impact_score * factor))
    suffix = ""
    if kind == "rural":
        suffix = " (boosted: your station serves a rural audience profile)"
    elif kind == "urban":
        suffix = " (boosted: your station serves an urban audience profile)"
    return rec.model_copy(update={
        "message": rec.message + suffix,
        "impact_score": round(new_impact, 4),
    })


def _audience_profile_recs(
    profile: StationProfile,
    segments: list[Segment],
    programme_input: ProgrammeInput,
) -> list[Recommendation]:
    extras: list[Recommendation] = []

    if profile.is_rural() and profile.preferred_languages:
        langs = ", ".join(profile.preferred_languages)
        audience_word = profile.audience_type or "rural"
        extras.append(Recommendation(
            category="cultural_audience",
            message=(
                f"Your station serves a {audience_word} audience. Consider "
                f"local-language segments ({langs}) — rural FM trust is "
                "significantly higher with local-language programming."
            ),
            impact_score=0.7,
            source="Antwi-Boateng et al., Cogent Arts & Humanities, 2023",
            confidence="user-provided",
            severity="suggestion",
            based_on_history=True,
            recommendation_id="USR-LANG",
        ))
    elif profile.is_rural() and not profile.preferred_languages:
        extras.append(Recommendation(
            category="cultural_audience",
            message=(
                "Your station profile is rural. Local-language and "
                "agricultural content has been prioritised in the "
                "recommendations above."
            ),
            impact_score=0.55,
            source="Antwi-Boateng et al., Cogent Arts & Humanities, 2023",
            confidence="user-provided",
            severity="tip",
            based_on_history=True,
            recommendation_id="USR-RURAL",
        ))

    if profile.is_urban() and programme_input.programme_type in {
        ProgrammeType.MORNING_SHOW, ProgrammeType.DRIVE_TIME
    }:
        extras.append(Recommendation(
            category="urban_audience",
            message=(
                "Urban audience profile applied. Traffic, commute and "
                "social-media engagement recommendations have been "
                "prioritised."
            ),
            impact_score=0.5,
            source="user-provided station statistics",
            confidence="user-provided",
            severity="tip",
            based_on_history=True,
            recommendation_id="USR-URBAN",
        ))

    return extras


def _low_window_content_tip(
    profile: StationProfile, segments: list[Segment]
) -> Recommendation | None:
    if not profile.low_windows:
        return None
    HEAVY = {SegmentType.INTERVIEW, SegmentType.PHONE_IN_SEGMENT,
             SegmentType.SCRIPTED_REPORT, SegmentType.NEWS}
    for s in segments:
        if s.type not in HEAVY:
            continue
        start = _hhmm(s.start_time)
        end = _hhmm(s.end_time)
        for lo, hi in profile.low_windows:
            if overlaps((lo, hi), start, end):
                window_label = f"{lo // 60:02d}:{lo % 60:02d}-{hi // 60:02d}:{hi % 60:02d}"
                return Recommendation(
                    category="placement_audience",
                    message=(
                        f"Segment '{s.name}' airs during a window you've marked "
                        f"as low-listenership ({window_label}). Consider moving "
                        "high-value content to a peak window."
                    ),
                    impact_score=0.55,
                    source="user-provided station statistics",
                    confidence="user-provided",
                    severity="suggestion",
                    based_on_history=True,
                    recommendation_id="USR-LOWPLACE",
                )
    return None


# ───────────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────────

def _hhmm(t: str) -> int:
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def _get_value(user_stats: dict[str, Any], key: str) -> str | None:
    stat = user_stats.get(key)
    if stat is None:
        return None
    value = getattr(stat, "stat_value", None)
    if value is None and isinstance(stat, dict):
        value = stat.get("stat_value")
    if not value:
        return None
    return str(value).strip() or None
