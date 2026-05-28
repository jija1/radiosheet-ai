from __future__ import annotations

from app.ai.recommendations.engine import generate_recommendations as _new_engine
from app.api.v1.runsheet.schemas import (
    ProgrammeInput,
    Recommendation,
    Segment,
    SegmentType,
    TalkMusicPreference,
)

# ---------------------------------------------------------------------------
# Weights (must sum to 1.0)
# ---------------------------------------------------------------------------

_WEIGHTS: dict[str, float] = {
    "balance":    0.30,
    "advert":     0.25,
    "placement":  0.25,
    "transition": 0.20,
}

# Trigger thresholds — dimensions below these scores produce recommendations
_THRESHOLDS: dict[str, float] = {
    "balance":    0.75,
    "advert":     0.70,
    "placement":  0.75,
    "transition": 0.801,  # ensures score of 0.8 (1 violation) triggers naturally
}

# Target music ratio for each preference (talk ratio = 1 - music ratio)
_MUSIC_TARGET: dict[TalkMusicPreference, float] = {
    TalkMusicPreference.HEAVY_MUSIC: 0.65,
    TalkMusicPreference.BALANCED:    0.50,
    TalkMusicPreference.TALK_HEAVY:  0.35,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_recommendations(
    segments: list[Segment],
    programme_input: ProgrammeInput,
    user_stats: dict | None = None,
    deep_dive: bool = False,
    station_profile: object | None = None,
    user_settings: object | None = None,
) -> tuple[list[Recommendation], float]:
    """
    Score four weighted dimensions (backward-compatible), merge with new engine
    recommendations, and return (recommendations, composite_score).

    No minimum count is enforced. Empty list is valid.

    Optional user_stats, deep_dive, station_profile and user_settings are
    forwarded to the new engine.
    """
    # 1. Score every dimension
    balance_score    = _score_balance(segments, programme_input)
    advert_score     = _score_advert(segments, programme_input)
    placement_score  = _score_placement(segments, programme_input)
    transition_score = _score_transition(segments)

    # 2. Composite weighted sum (used for RunSheetStats.score)
    composite = (
        balance_score    * _WEIGHTS["balance"] +
        advert_score     * _WEIGHTS["advert"] +
        placement_score  * _WEIGHTS["placement"] +
        transition_score * _WEIGHTS["transition"]
    )

    # 3. Old dimension recommendations (categories: balance, advert, placement, transition)
    all_dims: list[tuple[str, float, float, str]] = [
        ("balance",    balance_score,    _THRESHOLDS["balance"],
         _msg_balance(segments, programme_input, balance_score)),
        ("advert",     advert_score,     _THRESHOLDS["advert"],
         _msg_advert(segments, advert_score)),
        ("placement",  placement_score,  _THRESHOLDS["placement"],
         _msg_placement(segments, programme_input, placement_score)),
        ("transition", transition_score, _THRESHOLDS["transition"],
         _msg_transition(segments, transition_score)),
    ]
    old_recs: list[Recommendation] = [
        Recommendation(category=cat, message=msg, impact_score=round(score, 4))
        for cat, score, threshold, msg in all_dims
        if score < threshold
    ]

    # 4. New engine recommendations (different category set — no overlap)
    new_recs = _new_engine(
        segments,
        programme_input,
        user_stats=user_stats,
        deep_dive=deep_dive,
        station_profile=station_profile,
        user_settings=user_settings,
    )

    # 5. Merge: old categories take precedence; new recs add unique categories
    old_categories = {r.category for r in old_recs}
    merged = list(old_recs) + [r for r in new_recs if r.category not in old_categories]

    _SEVERITY_ORDER = {"critical": 0, "warning": 1, "suggestion": 2, "tip": 3}
    merged.sort(key=lambda r: (_SEVERITY_ORDER.get(r.severity, 99), -r.impact_score))

    return merged, round(composite, 4)


# ---------------------------------------------------------------------------
# Dimension 1: talk_music_balance  (weight 0.30)
# ---------------------------------------------------------------------------

def _score_balance(segments: list[Segment], programme_input: ProgrammeInput) -> float:
    music_mins = sum(s.duration_minutes for s in segments if s.type == SegmentType.MUSIC)
    talk_mins  = sum(s.duration_minutes for s in segments if s.type == SegmentType.TALK)
    content_total = music_mins + talk_mins

    if content_total == 0:
        return 1.0  # no music/talk segments; nothing to penalise

    actual_music = music_mins / content_total
    target_music = _MUSIC_TARGET[programme_input.talk_music_preference]
    deviation    = abs(actual_music - target_music)

    if deviation <= 0.05:
        return 1.0

    # Linear decay: 1.0 at deviation=0.05, 0.0 at deviation=0.55
    return max(0.0, 1.0 - (deviation - 0.05) / 0.50)


def _msg_balance(
    segments: list[Segment],
    programme_input: ProgrammeInput,
    score: float,
) -> str:
    music_mins = sum(s.duration_minutes for s in segments if s.type == SegmentType.MUSIC)
    talk_mins  = sum(s.duration_minutes for s in segments if s.type == SegmentType.TALK)
    total = music_mins + talk_mins

    if total == 0:
        return "Add music and talk segments to achieve a balanced programme."

    actual_pct = music_mins / total * 100
    target_pct = _MUSIC_TARGET[programme_input.talk_music_preference] * 100
    pref_label = programme_input.talk_music_preference.value.replace("_", " ")

    if actual_pct > target_pct:
        extra_talk = int((actual_pct - target_pct) / 100 * total)
        return (
            f"Music fills {actual_pct:.0f}% of content but your '{pref_label}' preference "
            f"targets {target_pct:.0f}%. Add approximately {extra_talk} minutes of talk to rebalance."
        )
    else:
        extra_music = int((target_pct - actual_pct) / 100 * total)
        return (
            f"Music fills {actual_pct:.0f}% of content but your '{pref_label}' preference "
            f"targets {target_pct:.0f}%. Add approximately {extra_music} minutes of music to rebalance."
        )


# ---------------------------------------------------------------------------
# Dimension 2: advert_distribution  (weight 0.25)
# ---------------------------------------------------------------------------

def _score_advert(segments: list[Segment], programme_input: ProgrammeInput) -> float:
    start_mins = _hhmm_to_minutes(programme_input.start_time)
    advert_offsets = sorted(
        _hhmm_to_minutes(s.start_time) - start_mins
        for s in segments
        if s.type == SegmentType.ADVERT
    )

    if len(advert_offsets) <= 1:
        return 0.0  # cannot measure distribution with 0 or 1 blocks

    gaps = [
        advert_offsets[i + 1] - advert_offsets[i]
        for i in range(len(advert_offsets) - 1)
    ]
    mean_gap = sum(gaps) / len(gaps)

    if mean_gap == 0:
        return 0.0

    max_rel_dev = max(abs(g - mean_gap) / mean_gap for g in gaps)

    if max_rel_dev <= 0.20:
        return 1.0

    # Linear decay: 1.0 at rel_dev=0.20, 0.0 at rel_dev=1.0
    return max(0.0, 1.0 - (max_rel_dev - 0.20) / 0.80)


def _msg_advert(segments: list[Segment], score: float) -> str:
    n = sum(1 for s in segments if s.type == SegmentType.ADVERT)
    if n <= 1:
        return (
            "Only one advert block detected. Add more advert blocks and space them "
            "evenly to maintain listener engagement throughout the programme."
        )
    return (
        f"The {n} advert blocks are unevenly distributed. Space them at regular intervals "
        f"across the programme to prevent listener fatigue and maximise advertiser reach."
    )


# ---------------------------------------------------------------------------
# Dimension 3: engagement_placement  (weight 0.25)
# ---------------------------------------------------------------------------

_HIGH_ENGAGEMENT = {SegmentType.NEWS, SegmentType.WEATHER}


def _score_placement(
    segments: list[Segment], programme_input: ProgrammeInput
) -> float:
    start_mins     = _hhmm_to_minutes(programme_input.start_time)
    first_third_end = start_mins + programme_input.total_duration_minutes // 3

    high_eng = [s for s in segments if s.type in _HIGH_ENGAGEMENT]
    if not high_eng:
        return 1.0  # no high-engagement segments to misplace

    correct = sum(
        1 for s in high_eng
        if _hhmm_to_minutes(s.start_time) < first_third_end
    )
    return correct / len(high_eng)


def _msg_placement(
    segments: list[Segment],
    programme_input: ProgrammeInput,
    score: float,
) -> str:
    start_mins      = _hhmm_to_minutes(programme_input.start_time)
    first_third_end = start_mins + programme_input.total_duration_minutes // 3
    cutoff_time     = _minutes_to_hhmm(first_third_end)

    misplaced = [
        s for s in segments
        if s.type in _HIGH_ENGAGEMENT
        and _hhmm_to_minutes(s.start_time) >= first_third_end
    ]
    if misplaced:
        names = ", ".join(f"'{s.name}'" for s in misplaced[:3])
        return (
            f"Move {names} to before {cutoff_time}. News and weather perform best "
            f"in the first third of the programme when listener attention is highest."
        )
    return (
        f"Place all news and weather segments before {cutoff_time} (first third) "
        f"to maximise listener retention during high-attention opening minutes."
    )


# ---------------------------------------------------------------------------
# Dimension 4: transition_quality  (weight 0.20)
# ---------------------------------------------------------------------------

def _score_transition(segments: list[Segment]) -> float:
    if not segments:
        return 1.0

    violations = 0
    i = 0
    while i < len(segments):
        run = 1
        while i + run < len(segments) and segments[i + run].type == segments[i].type:
            run += 1
        if run > 2:
            violations += 1
        i += run

    return max(0.0, 1.0 - violations * 0.2)


def _msg_transition(segments: list[Segment], score: float) -> str:
    # Find the first offending run to name it specifically
    i = 0
    while i < len(segments):
        run = 1
        while i + run < len(segments) and segments[i + run].type == segments[i].type:
            run += 1
        if run > 2:
            seg_type = segments[i].type.value
            return (
                f"Found a run of {run} consecutive '{seg_type}' segments starting at "
                f"{segments[i].start_time}. Break up same-type runs with a different "
                f"segment type to improve programme flow and listener engagement."
            )
        i += run

    return (
        "Avoid placing more than 2 consecutive segments of the same type. "
        "Varying segment types maintains listener interest and improves programme flow."
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hhmm_to_minutes(time_str: str) -> int:
    h, m = time_str.split(":")
    return int(h) * 60 + int(m)


def _minutes_to_hhmm(minutes: int) -> str:
    minutes = minutes % (24 * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"
