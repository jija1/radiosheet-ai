"""Time-of-day music mood mapping for Ghana FM radio."""
from __future__ import annotations

_MOOD_SLOTS: list[tuple[int, int, dict]] = [
    (0 * 60,  4 * 60, {
        "energy_level":      "low_energy",
        "preferred_genres":  ["ambient", "slow", "instrumental"],
        "notes":             "Late night/very early: low energy, ambient content preferred.",
    }),
    (4 * 60,  6 * 60, {
        "energy_level":      "low_energy",
        "preferred_genres":  ["inspirational", "ambient", "gospel"],
        "notes":             "Pre-dawn: gentle, inspirational content — dawn listeners waking up.",
    }),
    (6 * 60, 10 * 60, {
        "energy_level":      "building_energy",
        "preferred_genres":  ["highlife", "uplifting", "gospel", "afrobeats"],
        "notes":             "Morning build: energy should rise through the slot for commuters.",
    }),
    (10 * 60, 14 * 60, {
        "energy_level":      "high_energy",
        "preferred_genres":  ["popular_hits", "dance", "afrobeats", "highlife"],
        "notes":             "Mid-morning/midday: peak energy, popular and upbeat content.",
    }),
    (14 * 60, 17 * 60, {
        "energy_level":      "moderate_energy",
        "preferred_genres":  ["conversation_friendly", "soul", "RnB"],
        "notes":             "Afternoon: moderate energy, talk-friendly music backdrop.",
    }),
    (17 * 60, 20 * 60, {
        "energy_level":      "high_energy",
        "preferred_genres":  ["hits", "afrobeats", "sports_appropriate", "highlife"],
        "notes":             "Evening drive: high energy for commuters and sports audience.",
    }),
    (20 * 60, 23 * 60, {
        "energy_level":      "mellow",
        "preferred_genres":  ["RnB", "soul", "slow_jams"],
        "notes":             "Evening: mellow, RnB/soul for wind-down listening.",
    }),
    (23 * 60, 24 * 60, {
        "energy_level":      "low_energy",
        "preferred_genres":  ["ambient", "slow", "instrumental"],
        "notes":             "Late night: low energy, ambient preferred.",
    }),
]

_SUNDAY_MORNING_OVERRIDE = {
    "energy_level":      "gospel_focused",
    "preferred_genres":  ["gospel", "worship", "inspirational"],
    "notes":             "Sunday morning: primary gospel/church window in Ghana.",
}

_FRIDAY_AFTERNOON_OVERRIDE = {
    "energy_level":      "moderate_energy",
    "preferred_genres":  ["cultural", "news", "community"],
    "notes":             "Friday 12:00–14:30: Jumu'ah prayer window — lower energy, fewer adverts.",
}

_SATURDAY_OVERRIDE = {
    "energy_level":      "family_friendly",
    "preferred_genres":  ["family", "highlife", "popular"],
    "notes":             "Saturday afternoon: family co-listening peak.",
}


def _hhmm_to_minutes(time_str: str) -> int:
    h, m = time_str.split(":")
    return int(h) * 60 + int(m)


def get_mood_advice(time_str: str, day_of_week: int) -> dict:
    """
    Return mood advice for the given time and day.
    day_of_week: 0=Monday … 6=Sunday.
    """
    mins = _hhmm_to_minutes(time_str) % (24 * 60)

    # Day-of-week overrides
    if day_of_week == 6 and 5 * 60 <= mins < 12 * 60:
        return _SUNDAY_MORNING_OVERRIDE.copy()
    if day_of_week == 4 and 12 * 60 <= mins < 14 * 60 + 30:
        return _FRIDAY_AFTERNOON_OVERRIDE.copy()
    if day_of_week == 5 and 12 * 60 <= mins < 18 * 60:
        return _SATURDAY_OVERRIDE.copy()

    for slot_start, slot_end, advice in _MOOD_SLOTS:
        if slot_start <= mins < slot_end:
            return advice.copy()

    # Fallback (shouldn't be reached)
    return _MOOD_SLOTS[-1][2].copy()
