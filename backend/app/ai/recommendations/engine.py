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
from app.api.v1.runsheet.schemas import ProgrammeInput, Recommendation, Segment

_SEVERITY_ORDER = {"critical": 0, "warning": 1, "suggestion": 2, "tip": 3}


def generate_recommendations(
    segments: list[Segment],
    programme_input: ProgrammeInput,
    user_stats: dict[str, Any] | None = None,
    deep_dive: bool = False,
) -> list[Recommendation]:
    """
    Run every library check. Return deduplicated recommendations sorted by
    severity (critical first) then impact_score descending.
    No minimum count enforced — empty list is valid.

    user_stats: optional dict mapping stat_key -> UserStatistic-like object
                (must have .stat_value attribute). When provided,
                local_cultural_note and peak_listening_window are surfaced as
                tip recommendations; custom_recommendation is always appended.

    deep_dive: when True, also append a mood-advisor tip for the broadcast
               start time.
    """
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


def _get_value(user_stats: dict[str, Any], key: str) -> str | None:
    stat = user_stats.get(key)
    if stat is None:
        return None
    value = getattr(stat, "stat_value", None)
    if not value:
        return None
    return str(value).strip() or None
