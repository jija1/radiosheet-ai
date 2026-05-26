from __future__ import annotations

import uuid

from app.api.v1.runsheet.schemas import (
    Conflict,
    ProgrammeInput,
    ProgrammeType,
    Segment,
    SegmentType,
)

# Segment types that must not be auto-reduced (C002 fix)
_MANDATORY = {SegmentType.INTRO, SegmentType.STATION_ID, SegmentType.CLOSE}

# Colour for auto-inserted segments
_COLOURS: dict[SegmentType, str] = {
    SegmentType.TALK:       "#3b82f6",
    SegmentType.STATION_ID: "#06b6d4",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_conflicts(
    segments: list[Segment],
    programme_input: ProgrammeInput,
    user_settings: dict | None = None,
) -> list[Conflict]:
    settings = user_settings or {}
    conflicts: list[Conflict] = []
    conflicts.extend(_check_c001(segments))
    conflicts.extend(_check_c002(segments, programme_input))
    conflicts.extend(_check_c003(segments, programme_input))
    conflicts.extend(_check_c004(segments, programme_input))
    conflicts.extend(_check_c005(segments))
    conflicts.extend(_check_c006(segments, programme_input))
    conflicts.extend(_check_c007(segments, programme_input))
    conflicts.extend(_check_c008(segments, programme_input))
    conflicts.extend(_check_c009(segments, programme_input))
    conflicts.extend(_check_c010(segments, programme_input, settings))
    return conflicts


def apply_fix(
    segments: list[Segment],
    conflict: Conflict,
    programme_input: ProgrammeInput,
) -> list[Segment]:
    action = conflict.suggested_fix.get("action")
    if action == "insert":
        return _fix_insert(segments, conflict.suggested_fix)
    if action == "reduce":
        return _fix_reduce(segments, conflict.suggested_fix)
    if action == "shift":
        return _fix_shift(segments, conflict.suggested_fix)
    return list(segments)


# ---------------------------------------------------------------------------
# C001 — Consecutive advert blocks
# ---------------------------------------------------------------------------

def _check_c001(segments: list[Segment]) -> list[Conflict]:
    """
    Trigger: two Advert segments with no intervening non-Advert of >= 3 min.
    Reports one conflict per offending advert pair.
    """
    conflicts: list[Conflict] = []
    reported: set[tuple[int, int]] = set()
    n = len(segments)

    for i in range(n):
        if segments[i].type != SegmentType.ADVERT:
            continue

        has_qualifying_sep = False
        for j in range(i + 1, n):
            seg = segments[j]
            if seg.type == SegmentType.ADVERT:
                pair = (i, j)
                if pair not in reported and not has_qualifying_sep:
                    reported.add(pair)
                    conflicts.append(
                        Conflict(
                            rule_id="C001",
                            severity="warning",
                            message=(
                                f"Consecutive advert blocks: '{segments[i].name}' "
                                f"and '{segments[j].name}' without adequate separation"
                            ),
                            affected_segment_ids=[segments[i].id, segments[j].id],
                            suggested_fix={
                                "action": "insert",
                                "type": "talk",
                                "duration_minutes": 3,
                                "position": "between_adverts",
                                "affected_index": j,
                            },
                        )
                    )
                break
            else:
                if seg.duration_minutes >= 3:
                    has_qualifying_sep = True
                    break
                # Short non-advert: keep scanning for the next advert

    return conflicts


# ---------------------------------------------------------------------------
# C002 — Total duration overrun
# ---------------------------------------------------------------------------

def _check_c002(
    segments: list[Segment],
    programme_input: ProgrammeInput,
) -> list[Conflict]:
    """
    Trigger: sum of all segment durations > total_duration_minutes + 1 min
    (CLAUDE.md says "> total_duration_minutes + 60 seconds").
    """
    total_dur = sum(s.duration_minutes for s in segments)
    limit = programme_input.total_duration_minutes
    excess = total_dur - limit

    if excess <= 1:
        return []

    non_mandatory = [s for s in segments if s.type not in _MANDATORY]
    if not non_mandatory:
        return []

    longest = max(non_mandatory, key=lambda s: s.duration_minutes)
    return [
        Conflict(
            rule_id="C002",
            severity="blocking",
            message=(
                f"Total duration {total_dur} min exceeds programme limit "
                f"{limit} min by {excess} min"
            ),
            affected_segment_ids=[longest.id],
            suggested_fix={
                "action": "reduce",
                "target_segment_id": longest.id,
                "reduce_by_minutes": excess,
            },
        )
    ]


# ---------------------------------------------------------------------------
# C003 — Missing station identification
# ---------------------------------------------------------------------------

def _check_c003(
    segments: list[Segment],
    programme_input: ProgrammeInput,
) -> list[Conflict]:
    """
    Trigger: no StationID in first 15 min, or no StationID in any subsequent
    30-minute window. Reports one conflict per offending window.
    """
    conflicts: list[Conflict] = []
    start_mins = _hhmm_to_minutes(programme_input.start_time)
    total = programme_input.total_duration_minutes

    # Positions of station IDs relative to programme start (in minutes)
    sid_offsets = [
        _hhmm_to_minutes(s.start_time) - start_mins
        for s in segments
        if s.type == SegmentType.STATION_ID
    ]

    # First 15-minute window
    if not any(0 <= p < 15 for p in sid_offsets):
        conflicts.append(
            Conflict(
                rule_id="C003",
                severity="warning",
                message="No station identification within the first 15 minutes",
                affected_segment_ids=[],
                suggested_fix={
                    "action": "insert",
                    "type": "station_id",
                    "duration_minutes": 2,
                    "at_minute": 14,
                },
            )
        )

    # Subsequent 30-minute windows
    window_start = 15
    while window_start < total:
        window_end = min(window_start + 30, total)
        if not any(window_start <= p < window_end for p in sid_offsets):
            midpoint = (window_start + window_end) // 2
            conflicts.append(
                Conflict(
                    rule_id="C003",
                    severity="warning",
                    message=(
                        f"No station identification in window "
                        f"{window_start}–{window_end} minutes"
                    ),
                    affected_segment_ids=[],
                    suggested_fix={
                        "action": "insert",
                        "type": "station_id",
                        "duration_minutes": 2,
                        "at_minute": midpoint,
                    },
                )
            )
        window_start += 30

    return conflicts


# ---------------------------------------------------------------------------
# C004 — Excessive advert density
# ---------------------------------------------------------------------------

def _check_c004(
    segments: list[Segment],
    programme_input: ProgrammeInput,
) -> list[Conflict]:
    """Trigger: total advert duration > 20% of total_duration_minutes."""
    total = programme_input.total_duration_minutes
    advert_total = sum(
        s.duration_minutes for s in segments if s.type == SegmentType.ADVERT
    )

    if advert_total <= total * 0.20:
        return []

    advert_segs = [s for s in segments if s.type == SegmentType.ADVERT]
    if not advert_segs:
        return []

    longest = max(advert_segs, key=lambda s: s.duration_minutes)
    target_total = int(total * 0.18)
    reduce_by = advert_total - target_total

    return [
        Conflict(
            rule_id="C004",
            severity="warning",
            message=(
                f"Advert density {advert_total / total * 100:.1f}% exceeds 20% limit "
                f"({advert_total} min of {total} min total)"
            ),
            affected_segment_ids=[longest.id],
            suggested_fix={
                "action": "reduce",
                "target_segment_id": longest.id,
                "reduce_by_minutes": reduce_by,
            },
        )
    ]


# ---------------------------------------------------------------------------
# C005 — Segment overlap
# ---------------------------------------------------------------------------

def _check_c005(segments: list[Segment]) -> list[Conflict]:
    """Trigger: any segment start_time < previous segment end_time."""
    conflicts: list[Conflict] = []
    for i in range(1, len(segments)):
        prev_end   = _hhmm_to_minutes(segments[i - 1].end_time)
        curr_start = _hhmm_to_minutes(segments[i].start_time)
        if curr_start < prev_end:
            conflicts.append(
                Conflict(
                    rule_id="C005",
                    severity="blocking",
                    message=(
                        f"'{segments[i].name}' starts at {segments[i].start_time} "
                        f"but '{segments[i - 1].name}' ends at {segments[i - 1].end_time}"
                    ),
                    affected_segment_ids=[segments[i - 1].id, segments[i].id],
                    suggested_fix={
                        "action": "shift",
                        "target_segment_id": segments[i].id,
                        "new_start_time": segments[i - 1].end_time,
                    },
                )
            )
    return conflicts


# ---------------------------------------------------------------------------
# C006 — Programme / Time Mismatch
# ---------------------------------------------------------------------------

_C006_WINDOWS: dict[ProgrammeType, list[tuple[int, int]]] = {
    ProgrammeType.MORNING_SHOW:   [(4 * 60, 10 * 60)],
    ProgrammeType.DRIVE_TIME:     [(6 * 60, 9 * 60), (15 * 60, 19 * 60)],
    ProgrammeType.NEWS_HOUR:      [(4 * 60, 2 * 60 + 24 * 60)],  # any except 02:00-04:00
    ProgrammeType.FARMER_SHOW:    [(4 * 60, 7 * 60), (17 * 60, 19 * 60)],
    ProgrammeType.RELIGIOUS_SHOW: [(5 * 60, 9 * 60), (18 * 60, 21 * 60)],
}

_C006_RECOMMENDED: dict[ProgrammeType, str] = {
    ProgrammeType.MORNING_SHOW:   "05:00–10:00",
    ProgrammeType.DRIVE_TIME:     "06:00–09:00 or 15:00–19:00",
    ProgrammeType.NEWS_HOUR:      "any time except 02:00–04:00 (dead air)",
    ProgrammeType.FARMER_SHOW:    "04:00–07:00 or 17:00–19:00",
    ProgrammeType.RELIGIOUS_SHOW: "05:00–09:00 or 18:00–21:00",
}


def _check_c006(
    segments: list[Segment],
    programme_input: ProgrammeInput,
) -> list[Conflict]:
    windows = _C006_WINDOWS.get(programme_input.programme_type)
    if windows is None:
        return []

    start_mins = _hhmm_to_minutes(programme_input.start_time)

    # Special case: NEWS_HOUR must NOT start between 02:00-04:00
    if programme_input.programme_type == ProgrammeType.NEWS_HOUR:
        if 2 * 60 <= start_mins < 4 * 60:
            return [Conflict(
                rule_id="C006",
                severity="warning",
                message=(
                    "News Hour scheduled in dead-air window 02:00–04:00. "
                    "Audience reach is negligible in this slot."
                ),
                affected_segment_ids=[],
                suggested_fix={
                    "action": "reschedule",
                    "recommended_start": "06:00",
                    "source": "GeoPoll Ghana Media Measurement Report 2018",
                },
            )]
        return []

    in_window = any(lo <= start_mins < hi for lo, hi in windows)
    if not in_window:
        recommended = _C006_RECOMMENDED[programme_input.programme_type]
        return [Conflict(
            rule_id="C006",
            severity="warning",
            message=(
                f"{programme_input.programme_type.value.replace('_', ' ').title()} "
                f"starts at {programme_input.start_time}, outside recommended window "
                f"({recommended}). Audience reach may be significantly reduced."
            ),
            affected_segment_ids=[],
            suggested_fix={
                "action": "reschedule",
                "recommended_window": recommended,
                "source": "GeoPoll Ghana Media Measurement Report 2018",
            },
        )]
    return []


# ---------------------------------------------------------------------------
# C007 — Music Mood vs Time Mismatch  (informational — no auto-fix)
# ---------------------------------------------------------------------------

def _check_c007(
    segments: list[Segment],
    programme_input: ProgrammeInput,
) -> list[Conflict]:
    start_mins = _hhmm_to_minutes(programme_input.start_time)
    music_segs = [s for s in segments if s.type == SegmentType.MUSIC]
    if not music_segs:
        return []

    # High-energy music before 06:00 is mood-inappropriate
    early_music = [s for s in music_segs if _hhmm_to_minutes(s.start_time) < 6 * 60]
    if early_music:
        return [Conflict(
            rule_id="C007",
            severity="suggestion",
            message=(
                f"{len(early_music)} music segment(s) scheduled before 06:00. "
                "Pre-dawn listeners respond better to low-energy, ambient or "
                "inspirational music than high-energy tracks."
            ),
            affected_segment_ids=[s.id for s in early_music],
            suggested_fix={
                "action": "note",
                "note": "Consider ambient/inspirational music before 06:00.",
                "source": "industry best practice (audience mood-energy alignment)",
            },
        )]

    # Drive-time slots benefit from high-energy music; flag if drive-time programme
    # is missing any upbeat content (this is informational)
    if programme_input.programme_type == ProgrammeType.DRIVE_TIME:
        drive_start = _hhmm_to_minutes(programme_input.start_time)
        if drive_start >= 15 * 60:
            # Evening drive — flag if programme is very music-light
            music_total = sum(s.duration_minutes for s in music_segs)
            if music_total < 5 and programme_input.total_duration_minutes >= 30:
                return [Conflict(
                    rule_id="C007",
                    severity="suggestion",
                    message=(
                        "Evening drive-time has very little music. Listeners expect "
                        "energy-appropriate music during the commute window 15:00–19:00."
                    ),
                    affected_segment_ids=[],
                    suggested_fix={
                        "action": "note",
                        "note": "Add uplifting music segments during evening drive.",
                        "source": "industry best practice (audience mood-energy alignment)",
                    },
                )]
    return []


# ---------------------------------------------------------------------------
# C008 — Talk Fatigue
# ---------------------------------------------------------------------------

_ENGAGEMENT_TYPES = {SegmentType.VOX_POP, SegmentType.PHONE_IN_SEGMENT, SegmentType.INTERVIEW}
_DRIVE_TALK_LIMIT  = 5  # minutes in drive-time
_GENERAL_TALK_LIMIT = 8  # minutes any programme


def _check_c008(
    segments: list[Segment],
    programme_input: ProgrammeInput,
) -> list[Conflict]:
    conflicts: list[Conflict] = []
    is_drive_time = programme_input.programme_type == ProgrammeType.DRIVE_TIME

    for i, seg in enumerate(segments):
        if seg.type != SegmentType.TALK:
            continue

        limit = _DRIVE_TALK_LIMIT if is_drive_time else _GENERAL_TALK_LIMIT
        if seg.duration_minutes <= limit:
            continue

        seg_end = _hhmm_to_minutes(seg.end_time)

        # Check if an engagement segment starts within 3 minutes after this talk ends
        has_nearby_engagement = any(
            s.type in _ENGAGEMENT_TYPES
            and 0 <= _hhmm_to_minutes(s.start_time) - seg_end <= 3
            for s in segments
        )
        if not has_nearby_engagement:
            conflicts.append(Conflict(
                rule_id="C008",
                severity="warning",
                message=(
                    f"Talk segment '{seg.name}' is {seg.duration_minutes} min "
                    f"(limit {limit} min for {programme_input.programme_type.value.replace('_', ' ')}) "
                    "without an engagement segment within 3 minutes."
                ),
                affected_segment_ids=[seg.id],
                suggested_fix={
                    "action": "insert",
                    "type": "vox_pop",
                    "duration_minutes": 2,
                    "after_segment_id": seg.id,
                    "source": (
                        "Drive time listeners are ~30% more likely to change station "
                        "during unbroken talk segments over 5 minutes — industry best practice"
                    ),
                },
            ))

    return conflicts


# ---------------------------------------------------------------------------
# C009 — Missing Peak Engagement
# ---------------------------------------------------------------------------

def _check_c009(
    segments: list[Segment],
    programme_input: ProgrammeInput,
) -> list[Conflict]:
    pt = programme_input.programme_type
    if pt == ProgrammeType.MORNING_SHOW:
        window_start, window_end = 6 * 60 + 30, 9 * 60      # 06:30–09:00
        label = "Accra morning commute peak (06:30–09:00)"
    elif pt == ProgrammeType.DRIVE_TIME:
        window_start, window_end = 16 * 60 + 30, 18 * 60 + 30  # 16:30–18:30
        label = "Accra evening commute peak (16:30–18:30)"
    else:
        return []

    has_engagement = any(
        s.type in _ENGAGEMENT_TYPES
        and window_start <= _hhmm_to_minutes(s.start_time) < window_end
        for s in segments
    )

    # Only flag if the programme actually spans the window
    prog_start = _hhmm_to_minutes(programme_input.start_time)
    prog_end   = prog_start + programme_input.total_duration_minutes
    if prog_end <= window_start or prog_start >= window_end:
        return []

    if not has_engagement:
        return [Conflict(
            rule_id="C009",
            severity="suggestion",
            message=(
                f"No high-engagement segment (interview, phone-in, vox-pop) during "
                f"{label}. Engagement content during peak windows significantly boosts "
                "listener retention."
            ),
            affected_segment_ids=[],
            suggested_fix={
                "action": "insert",
                "type": "phone_in_segment",
                "duration_minutes": 5,
                "window": label,
                "source": "Accra commute peak data (Caradise Ghana Traffic Analysis 2026)",
            },
        )]
    return []


# ---------------------------------------------------------------------------
# C010 — Cultural Calendar Conflict
# ---------------------------------------------------------------------------

_GHANA_FIXED_HOLIDAYS: set[tuple[int, int]] = {
    (1,  1),   # New Year's Day
    (3,  6),   # Independence Day
    (5,  1),   # Workers' Day
    (7,  1),   # Republic Day
    (8,  4),   # Founders' Day
    (9, 21),   # Kwame Nkrumah Memorial Day
    (12, 25),  # Christmas Day
    (12, 26),  # Boxing Day
}

_ISLAMIC_EID_APPROX: dict[tuple[int, int], str] = {
    (2024, 4, 10): "Eid al-Fitr 2024",   (2024, 6, 17): "Eid al-Adha 2024",
    (2025, 3, 30): "Eid al-Fitr 2025",   (2025, 6,  7): "Eid al-Adha 2025",
    (2026, 3, 20): "Eid al-Fitr 2026",   (2026, 5, 27): "Eid al-Adha 2026",
    (2027, 3,  9): "Eid al-Fitr 2027",   (2027, 5, 17): "Eid al-Adha 2027",
    (2028, 2, 26): "Eid al-Fitr 2028",   (2028, 5,  5): "Eid al-Adha 2028",
}


def _is_ghana_holiday(d: object) -> str | None:
    """Return holiday name or None. d is a datetime.date."""
    from dateutil.easter import easter

    if (d.month, d.day) in _GHANA_FIXED_HOLIDAYS:
        _NAMES = {
            (1,  1): "New Year's Day",
            (3,  6): "Independence Day",
            (5,  1): "Workers' Day",
            (7,  1): "Republic Day",
            (8,  4): "Founders' Day",
            (9, 21): "Kwame Nkrumah Memorial Day",
            (12, 25): "Christmas Day",
            (12, 26): "Boxing Day",
        }
        return _NAMES.get((d.month, d.day))

    # Farmers' Day: first Friday of December
    if d.month == 12 and d.weekday() == 4 and d.day <= 7:
        return "Farmers' Day"

    # Easter
    easter_sunday = easter(d.year)
    from datetime import timedelta
    if d == easter_sunday - timedelta(days=2):
        return "Good Friday"
    if d == easter_sunday:
        return "Easter Sunday"
    if d == easter_sunday + timedelta(days=1):
        return "Easter Monday"

    # Islamic (approximate)
    key = (d.year, d.month, d.day)
    if key in _ISLAMIC_EID_APPROX:
        return _ISLAMIC_EID_APPROX[key]

    return None


def _check_c010(
    segments: list[Segment],
    programme_input: ProgrammeInput,
    user_settings: dict,
) -> list[Conflict]:
    cultural_enabled = user_settings.get("cultural_calendar_enabled", True)
    if not cultural_enabled:
        return []

    conflicts: list[Conflict] = []
    bd = programme_input.broadcast_date
    start_mins = _hhmm_to_minutes(programme_input.start_time)

    # Sunday morning (06:00-12:00): expect religious/gospel content
    if bd.weekday() == 6 and 6 * 60 <= start_mins < 12 * 60:
        is_religious = programme_input.programme_type == ProgrammeType.RELIGIOUS_SHOW
        if not is_religious:
            conflicts.append(Conflict(
                rule_id="C010",
                severity="suggestion",
                message=(
                    "Sunday morning programme (06:00–12:00) does not include religious "
                    "or gospel content. Sunday morning is the primary gospel/church "
                    "broadcasting window for Ghanaian radio."
                ),
                affected_segment_ids=[],
                suggested_fix={
                    "action": "insert",
                    "type": "talk",
                    "note": "Consider a gospel/devotional segment.",
                    "source": "Ghana public holidays (official government calendar)",
                },
            ))

    # Friday afternoon (12:00-15:00): prayer window consideration
    prog_end = start_mins + programme_input.total_duration_minutes
    friday_prayer_start, friday_prayer_end = 12 * 60, 15 * 60
    if bd.weekday() == 4 and start_mins < friday_prayer_end and prog_end > friday_prayer_start:
        advert_in_window = any(
            s.type == SegmentType.ADVERT
            and friday_prayer_start <= _hhmm_to_minutes(s.start_time) < friday_prayer_end
            for s in segments
        )
        if advert_in_window:
            conflicts.append(Conflict(
                rule_id="C010",
                severity="suggestion",
                message=(
                    "Advert segments detected during Friday afternoon prayer window "
                    "(12:00–15:00). Consider reducing commercial intensity during "
                    "Jumu'ah prayer time."
                ),
                affected_segment_ids=[],
                suggested_fix={
                    "action": "note",
                    "note": "Move adverts outside 12:00–15:00 on Fridays.",
                    "source": "Ghana public holidays (official government calendar)",
                },
            ))

    # Public holidays: suggest acknowledgement
    holiday_name = _is_ghana_holiday(bd)
    if holiday_name:
        has_acknowledgement = any(
            s.type in {SegmentType.TALK, SegmentType.DRAMA, SegmentType.SCRIPTED_REPORT}
            for s in segments
        )
        if not has_acknowledgement:
            conflicts.append(Conflict(
                rule_id="C010",
                severity="suggestion",
                message=(
                    f"Today is {holiday_name} — a Ghana public holiday. No talk or "
                    "feature segment found to acknowledge the occasion."
                ),
                affected_segment_ids=[],
                suggested_fix={
                    "action": "insert",
                    "type": "talk",
                    "duration_minutes": 3,
                    "note": f"Add a {holiday_name} acknowledgement segment.",
                    "source": "Ghana public holidays (official government calendar)",
                },
            ))

    return conflicts


# ---------------------------------------------------------------------------
# Fix appliers
# ---------------------------------------------------------------------------

def _fix_insert(segments: list[Segment], fix: dict) -> list[Segment]:
    """Insert a new segment using either affected_index (C001) or at_minute (C003)."""
    seg_type = SegmentType(fix["type"])
    duration = fix["duration_minutes"]

    if "affected_index" in fix:
        # C001 path: insert before the segment at the given index
        idx = fix["affected_index"]
        if 0 < idx <= len(segments):
            start_mins = _hhmm_to_minutes(segments[idx - 1].end_time)
        elif segments:
            start_mins = _hhmm_to_minutes(segments[0].start_time)
        else:
            start_mins = 0
    else:
        # C003 path: insert at the segment that contains at_minute
        at_minute = fix["at_minute"]
        prog_start = _hhmm_to_minutes(segments[0].start_time) if segments else 0
        target_abs = prog_start + at_minute

        # Find the first segment that starts at or after the target minute
        idx = len(segments)
        for i, seg in enumerate(segments):
            if _hhmm_to_minutes(seg.start_time) >= target_abs:
                idx = i
                break

        start_mins = target_abs

    colour   = _COLOURS.get(seg_type, "#3b82f6")
    name_map = {
        SegmentType.TALK:       "Talk Break",
        SegmentType.STATION_ID: "Station ID",
    }
    new_seg = Segment(
        id=str(uuid.uuid4()),
        name=name_map.get(seg_type, seg_type.value.replace("_", " ").title()),
        type=seg_type,
        start_time=_minutes_to_hhmm(start_mins),
        end_time=_minutes_to_hhmm(start_mins + duration),
        duration_minutes=duration,
        colour_hex=colour,
        presenter_notes="",
    )

    updated = list(segments)
    updated.insert(idx, new_seg)
    return _recalculate_times(updated)


def _fix_reduce(segments: list[Segment], fix: dict) -> list[Segment]:
    """Reduce the target segment's duration and cascade subsequent times."""
    target_id = fix["target_segment_id"]
    reduce_by = fix["reduce_by_minutes"]

    updated = []
    for seg in segments:
        if seg.id == target_id:
            new_dur = max(1, seg.duration_minutes - reduce_by)
            new_end = _minutes_to_hhmm(_hhmm_to_minutes(seg.start_time) + new_dur)
            updated.append(seg.model_copy(update={"duration_minutes": new_dur, "end_time": new_end}))
        else:
            updated.append(seg)

    return _recalculate_times(updated)


def _fix_shift(segments: list[Segment], fix: dict) -> list[Segment]:
    """Set target segment's start_time and cascade all subsequent segments."""
    target_id = fix["target_segment_id"]
    new_start = fix["new_start_time"]

    updated = []
    for seg in segments:
        if seg.id == target_id:
            start_mins = _hhmm_to_minutes(new_start)
            new_end    = _minutes_to_hhmm(start_mins + seg.duration_minutes)
            updated.append(seg.model_copy(update={"start_time": new_start, "end_time": new_end}))
        else:
            updated.append(seg)

    return _recalculate_times(updated)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _recalculate_times(segments: list[Segment]) -> list[Segment]:
    """Walk the list sequentially, stamping start/end from the first segment onward."""
    if not segments:
        return segments
    result: list[Segment] = []
    cursor = _hhmm_to_minutes(segments[0].start_time)
    for seg in segments:
        new_start = _minutes_to_hhmm(cursor)
        new_end   = _minutes_to_hhmm(cursor + seg.duration_minutes)
        result.append(seg.model_copy(update={"start_time": new_start, "end_time": new_end}))
        cursor += seg.duration_minutes
    return result


def _hhmm_to_minutes(time_str: str) -> int:
    h, m = time_str.split(":")
    return int(h) * 60 + int(m)


def _minutes_to_hhmm(minutes: int) -> str:
    minutes = minutes % (24 * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"
