"""Ghana cultural calendar — public holidays and weekly broadcast patterns."""
from __future__ import annotations

from datetime import date, timedelta

from dateutil.easter import easter

_FIXED_HOLIDAYS: dict[tuple[int, int], str] = {
    (1,  1):  "New Year's Day",
    (3,  6):  "Independence Day",
    (5,  1):  "Workers' Day",
    (7,  1):  "Republic Day",
    (8,  4):  "Founders' Day",
    (9, 21):  "Kwame Nkrumah Memorial Day",
    (12, 25): "Christmas Day",
    (12, 26): "Boxing Day",
}

_ISLAMIC_EID: dict[tuple[int, int, int], str] = {
    (2024, 4, 10): "Eid al-Fitr",   (2024, 6, 17): "Eid al-Adha",
    (2025, 3, 30): "Eid al-Fitr",   (2025, 6,  7): "Eid al-Adha",
    (2026, 3, 20): "Eid al-Fitr",   (2026, 5, 27): "Eid al-Adha",
    (2027, 3,  9): "Eid al-Fitr",   (2027, 5, 17): "Eid al-Adha",
    (2028, 2, 26): "Eid al-Fitr",   (2028, 5,  5): "Eid al-Adha",
}

_WEEKLY_PATTERNS: dict[int, dict] = {
    6: {  # Sunday
        "character": "gospel_focused",
        "notes": "Primary gospel/church broadcasting window for Ghanaian radio (06:00–12:00).",
        "preferred_content": ["gospel", "worship", "devotional", "scripture"],
    },
    4: {  # Friday
        "character": "prayer_consideration",
        "notes": "Jumu'ah prayer window 12:00–14:30 — reduce commercial intensity.",
        "preferred_content": ["news", "cultural", "community"],
    },
    5: {  # Saturday
        "character": "family_friendly",
        "notes": "Family co-listening peak — broad content mix recommended.",
        "preferred_content": ["music", "family", "entertainment"],
    },
}


def get_holiday_for_date(d: date) -> str | None:
    """Return Ghana public holiday name for d, or None."""
    if (d.month, d.day) in _FIXED_HOLIDAYS:
        return _FIXED_HOLIDAYS[(d.month, d.day)]

    # Farmers' Day: first Friday of December
    if d.month == 12 and d.weekday() == 4 and d.day <= 7:
        return "Farmers' Day"

    # Moveable Easter
    e_sunday = easter(d.year)
    if d == e_sunday - timedelta(days=2):
        return "Good Friday"
    if d == e_sunday:
        return "Easter Sunday"
    if d == e_sunday + timedelta(days=1):
        return "Easter Monday"

    # Islamic (approximate lookup)
    if (d.year, d.month, d.day) in _ISLAMIC_EID:
        return _ISLAMIC_EID[(d.year, d.month, d.day)]

    return None


def get_weekly_pattern(day_of_week: int) -> dict:
    """Return weekly broadcast pattern for day_of_week (0=Monday, 6=Sunday)."""
    return _WEEKLY_PATTERNS.get(day_of_week, {
        "character": "standard",
        "notes": "Standard broadcasting day.",
        "preferred_content": [],
    })
