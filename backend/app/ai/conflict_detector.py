from __future__ import annotations

import uuid

from app.api.v1.runsheet.schemas import (
    Conflict,
    ProgrammeInput,
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
) -> list[Conflict]:
    conflicts: list[Conflict] = []
    conflicts.extend(_check_c001(segments))
    conflicts.extend(_check_c002(segments, programme_input))
    conflicts.extend(_check_c003(segments, programme_input))
    conflicts.extend(_check_c004(segments, programme_input))
    conflicts.extend(_check_c005(segments))
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
# Fix appliers
# ---------------------------------------------------------------------------

def _fix_insert(segments: list[Segment], fix: dict) -> list[Segment]:
    """Insert a new segment before the segment at affected_index."""
    idx      = fix["affected_index"]
    seg_type = SegmentType(fix["type"])
    duration = fix["duration_minutes"]

    if 0 < idx <= len(segments):
        start_mins = _hhmm_to_minutes(segments[idx - 1].end_time)
    elif segments:
        start_mins = _hhmm_to_minutes(segments[0].start_time)
    else:
        start_mins = 0

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
