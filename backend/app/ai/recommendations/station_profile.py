"""
Station profile — Session K6.

Parses raw user statistics + user settings into a structured StationProfile
that the recommendations engine and conflict detector can read directly.

Pure rule-based logic. No ML, no LLM. All parsing is forgiving: invalid
input is skipped, never crashed on.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

_TIME_RANGE_RE = re.compile(
    r"\s*(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})\s*"
)

_RURAL_REGIONS = {
    "northern", "upper_east", "upper_west", "upper east", "upper west",
    "north_east", "north east", "savannah", "oti", "bono_east", "bono east",
    "ahafo", "western_north", "western north",
}


@dataclass
class StationProfile:
    """Structured station profile derived from raw user statistics + settings."""

    peak_windows: list[tuple[int, int]] = field(default_factory=list)
    low_windows: list[tuple[int, int]] = field(default_factory=list)
    low_windows_raw: list[str] = field(default_factory=list)
    audience_size_by_hour: dict[int, int] = field(default_factory=dict)
    top_programme_types: list[str] = field(default_factory=list)
    preferred_languages: list[str] = field(default_factory=list)
    local_notes: list[str] = field(default_factory=list)
    custom_recommendations: list[str] = field(default_factory=list)
    audience_type: str | None = None
    region: str | None = None

    # Raw strings retained for surfacing in messages
    peak_window_raw: str | None = None

    def has_any_data(self) -> bool:
        return bool(
            self.peak_windows or self.low_windows or self.audience_size_by_hour
            or self.top_programme_types or self.preferred_languages
            or self.local_notes or self.custom_recommendations
            or self.audience_type or self.region
        )

    def is_rural(self) -> bool:
        if (self.audience_type or "").lower() == "rural":
            return True
        if self.region and self.region.lower() in _RURAL_REGIONS:
            return True
        return False

    def is_urban(self) -> bool:
        return (self.audience_type or "").lower() == "urban"


def _parse_time_ranges(raw: str | None) -> list[tuple[int, int]]:
    """
    Parse strings like "06:00-09:00", "05:30-08:00,17:00-19:00",
    "06:00 - 09:00; 17:00 - 19:00". Returns list of (start_min, end_min) tuples.
    Invalid ranges are silently skipped.
    """
    if not raw or not isinstance(raw, str):
        return []
    out: list[tuple[int, int]] = []
    parts = re.split(r"[;,]", raw)
    for part in parts:
        m = _TIME_RANGE_RE.fullmatch(part)
        if not m:
            continue
        try:
            h1, m1, h2, m2 = (int(x) for x in m.groups())
        except (TypeError, ValueError):
            continue
        if not (0 <= h1 <= 23 and 0 <= h2 <= 23 and 0 <= m1 <= 59 and 0 <= m2 <= 59):
            continue
        start = h1 * 60 + m1
        end = h2 * 60 + m2
        if end <= start:
            continue
        out.append((start, end))
    return out


def _parse_audience_json(raw: str | None) -> dict[int, int]:
    if not raw or not isinstance(raw, str):
        return {}
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return {}
    if not isinstance(data, dict):
        return {}
    result: dict[int, int] = {}
    for k, v in data.items():
        try:
            hour = int(k)
            count = int(v)
        except (TypeError, ValueError):
            continue
        if 0 <= hour <= 23 and count >= 0:
            result[hour] = count
    return result


def _parse_csv(raw: str | None) -> list[str]:
    if not raw or not isinstance(raw, str):
        return []
    return [piece.strip() for piece in re.split(r"[;,]", raw) if piece.strip()]


def _stat_value(user_stats: dict[str, Any] | None, key: str) -> str | None:
    if not user_stats:
        return None
    stat = user_stats.get(key)
    if stat is None:
        return None
    value = getattr(stat, "stat_value", None)
    if value is None and isinstance(stat, dict):
        value = stat.get("stat_value")
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _stat_notes(user_stats: dict[str, Any] | None, key: str) -> str | None:
    if not user_stats:
        return None
    stat = user_stats.get(key)
    if stat is None:
        return None
    notes = getattr(stat, "notes", None)
    if notes is None and isinstance(stat, dict):
        notes = stat.get("notes")
    if notes is None:
        return None
    s = str(notes).strip()
    return s or None


def build_station_profile(
    user_stats: dict[str, Any] | None,
    user_settings: Any | None = None,
) -> StationProfile:
    """
    Build a StationProfile from raw user statistics (dict of stat_key ->
    UserStatistic-like) and a user settings object (e.g. User model).
    Robust to None / missing values / malformed strings.
    """
    profile = StationProfile()

    peak_raw = _stat_value(user_stats, "peak_listening_window")
    if peak_raw:
        profile.peak_window_raw = peak_raw
        profile.peak_windows = _parse_time_ranges(peak_raw)

    low_raw = _stat_value(user_stats, "low_listening_window")
    if low_raw:
        profile.low_windows_raw = _parse_csv(low_raw)
        profile.low_windows = _parse_time_ranges(low_raw)

    audience_raw = _stat_value(user_stats, "audience_size_by_hour")
    if audience_raw:
        profile.audience_size_by_hour = _parse_audience_json(audience_raw)

    top_raw = _stat_value(user_stats, "top_programme_types")
    if top_raw:
        profile.top_programme_types = _parse_csv(top_raw)

    langs_raw = _stat_value(user_stats, "preferred_languages")
    if langs_raw:
        profile.preferred_languages = _parse_csv(langs_raw)

    note_raw = _stat_value(user_stats, "local_cultural_note")
    if note_raw:
        profile.local_notes.append(note_raw)

    custom_raw = _stat_value(user_stats, "custom_recommendation")
    if custom_raw:
        profile.custom_recommendations.append(custom_raw)

    if user_settings is not None:
        audience = getattr(user_settings, "station_audience", None)
        if audience:
            profile.audience_type = str(audience).strip().lower() or None
        region = getattr(user_settings, "default_region", None)
        if region:
            profile.region = str(region).strip().lower() or None

    return profile


def overlaps(window: tuple[int, int], start: int, end: int) -> bool:
    """True if (start, end) and window overlap at all (exclusive-end)."""
    return not (end <= window[0] or start >= window[1])


def first_window_label(windows: list[tuple[int, int]]) -> str | None:
    """Human-readable label for the first window, or None."""
    if not windows:
        return None
    s, e = windows[0]
    return f"{s // 60:02d}:{s % 60:02d}-{e // 60:02d}:{e % 60:02d}"


def all_window_labels(windows: list[tuple[int, int]]) -> str:
    """Comma-separated labels for all windows."""
    return ", ".join(
        f"{s // 60:02d}:{s % 60:02d}-{e // 60:02d}:{e % 60:02d}"
        for s, e in windows
    )
