from __future__ import annotations

from app.api.v1.runsheet.schemas import (
    ComplianceResult,
    ComplianceViolation,
    ProgrammeInput,
    ProgrammeType,
    Segment,
    SegmentType,
)

# ---------------------------------------------------------------------------
# G005 — forbidden segment types per programme format
# ---------------------------------------------------------------------------

_FORBIDDEN_TYPES: dict[ProgrammeType, frozenset[SegmentType]] = {
    ProgrammeType.MUSIC_ONLY: frozenset({
        SegmentType.TALK,
        SegmentType.NEWS,
        SegmentType.INTERVIEW,
        SegmentType.VOX_POP,
        SegmentType.DRAMA,
        SegmentType.STORYTELLING,
        SegmentType.SCRIPTED_REPORT,
        SegmentType.PHONE_IN_SEGMENT,
    }),
    ProgrammeType.NEWS_HOUR: frozenset({
        SegmentType.DRAMA,
        SegmentType.STORYTELLING,
    }),
    ProgrammeType.MORNING_SHOW: frozenset(),
    ProgrammeType.DRIVE_TIME:   frozenset(),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_compliance(
    segments: list[Segment],
    programme_input: ProgrammeInput,
) -> ComplianceResult:
    violations: list[ComplianceViolation] = []
    violations.extend(_check_g001(segments, programme_input))
    violations.extend(_check_g002(segments, programme_input))
    violations.extend(_check_g003(segments, programme_input))
    violations.extend(_check_g004(segments))
    violations.extend(_check_g005(segments, programme_input))

    total_penalty = sum(v.penalty for v in violations)
    score = max(0, 100 - total_penalty)

    if score >= 90:
        risk = "compliant"
    elif score >= 70:
        risk = "moderate"
    else:
        risk = "high"

    return ComplianceResult(
        compliance_score=score,
        compliance_risk=risk,
        compliance_violations=violations,
    )


# ---------------------------------------------------------------------------
# G001 — Opening station identification (first 15 min)
# ---------------------------------------------------------------------------

def _check_g001(
    segments: list[Segment],
    programme_input: ProgrammeInput,
) -> list[ComplianceViolation]:
    start_mins = _hhmm_to_minutes(programme_input.start_time)
    has_early_sid = any(
        s.type == SegmentType.STATION_ID
        and (_hhmm_to_minutes(s.start_time) - start_mins) < 15
        for s in segments
    )
    if not has_early_sid:
        return [
            ComplianceViolation(
                rule_id="G001",
                severity="moderate",
                message="No station identification within the opening 15 minutes",
                penalty=10,
            )
        ]
    return []


# ---------------------------------------------------------------------------
# G002 — Periodic station identification (each subsequent 30-min window)
# ---------------------------------------------------------------------------

def _check_g002(
    segments: list[Segment],
    programme_input: ProgrammeInput,
) -> list[ComplianceViolation]:
    start_mins = _hhmm_to_minutes(programme_input.start_time)
    total = programme_input.total_duration_minutes

    sid_offsets = [
        _hhmm_to_minutes(s.start_time) - start_mins
        for s in segments
        if s.type == SegmentType.STATION_ID
    ]

    violations: list[ComplianceViolation] = []
    window_start = 15
    while window_start < total:
        window_end = min(window_start + 30, total)
        if not any(window_start <= p < window_end for p in sid_offsets):
            violations.append(
                ComplianceViolation(
                    rule_id="G002",
                    severity="low",
                    message=(
                        f"No station identification in the "
                        f"{window_start}–{window_end} minute window"
                    ),
                    penalty=3,
                )
            )
        window_start += 30

    return violations


# ---------------------------------------------------------------------------
# G003 — Advert duration limit (> 20% of programme)
# ---------------------------------------------------------------------------

def _check_g003(
    segments: list[Segment],
    programme_input: ProgrammeInput,
) -> list[ComplianceViolation]:
    total = programme_input.total_duration_minutes
    advert_total = sum(
        s.duration_minutes for s in segments if s.type == SegmentType.ADVERT
    )
    if advert_total > total * 0.20:
        pct = round(advert_total / total * 100, 1)
        return [
            ComplianceViolation(
                rule_id="G003",
                severity="high",
                message=(
                    f"Advert content ({advert_total} min, {pct}%) "
                    f"exceeds the 20% programme limit"
                ),
                penalty=25,
            )
        ]
    return []


# ---------------------------------------------------------------------------
# G004 — Advert separation (< 10 min between consecutive advert blocks)
# ---------------------------------------------------------------------------

def _check_g004(segments: list[Segment]) -> list[ComplianceViolation]:
    blocks: list[tuple[int, int]] = []
    in_block = False
    block_start = block_end = 0

    for seg in segments:
        if seg.type == SegmentType.ADVERT:
            if not in_block:
                block_start = _hhmm_to_minutes(seg.start_time)
                in_block = True
            block_end = _hhmm_to_minutes(seg.end_time)
        else:
            if in_block:
                blocks.append((block_start, block_end))
                in_block = False
    if in_block:
        blocks.append((block_start, block_end))

    for i in range(1, len(blocks)):
        gap = blocks[i][0] - blocks[i - 1][1]
        if gap < 10:
            return [
                ComplianceViolation(
                    rule_id="G004",
                    severity="moderate",
                    message=(
                        f"Advert blocks are separated by only {gap} minute(s) "
                        f"(minimum is 10 minutes)"
                    ),
                    penalty=10,
                )
            ]
    return []


# ---------------------------------------------------------------------------
# G005 — Programme classification (segment types vs declared format)
# ---------------------------------------------------------------------------

def _check_g005(
    segments: list[Segment],
    programme_input: ProgrammeInput,
) -> list[ComplianceViolation]:
    forbidden = _FORBIDDEN_TYPES.get(programme_input.programme_type, frozenset())
    bad_types = sorted(
        {s.type.value for s in segments if s.type in forbidden}
    )
    if bad_types:
        return [
            ComplianceViolation(
                rule_id="G005",
                severity="low",
                message=(
                    f"Programme type '{programme_input.programme_type.value}' "
                    f"contains inconsistent segment types: {', '.join(bad_types)}"
                ),
                penalty=3,
            )
        ]
    return []


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

def _hhmm_to_minutes(time_str: str) -> int:
    h, m = time_str.split(":")
    return int(h) * 60 + int(m)
