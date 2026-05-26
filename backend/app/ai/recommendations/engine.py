"""
New recommendations engine — rule-based, context-aware, no forced minimum.
Produces recommendations with source, confidence, severity, and based_on_history fields.
Categories used: pacing, engagement, growth, cultural, monetisation, compliance.
(Old scorer categories: balance, advert, placement, transition — kept in scorer.py.)
"""
from __future__ import annotations

from app.ai.recommendations.library import LIBRARY
from app.api.v1.runsheet.schemas import ProgrammeInput, Recommendation, Segment

_SEVERITY_ORDER = {"critical": 0, "warning": 1, "suggestion": 2, "tip": 3}


def generate_recommendations(
    segments: list[Segment],
    programme_input: ProgrammeInput,
) -> list[Recommendation]:
    """
    Run every library check. Return deduplicated recommendations sorted by
    severity (critical first) then impact_score descending.
    No minimum count enforced — empty list is valid.
    """
    fired: list[Recommendation] = []
    for entry in LIBRARY:
        rec = entry["fn"](segments, programme_input)
        if rec is not None:
            fired.append(rec)

    # Deduplicate by category: keep highest impact_score per category
    best: dict[str, Recommendation] = {}
    for rec in fired:
        if rec.category not in best or rec.impact_score > best[rec.category].impact_score:
            best[rec.category] = rec

    deduped = list(best.values())
    deduped.sort(
        key=lambda r: (_SEVERITY_ORDER.get(r.severity, 99), -r.impact_score)
    )
    return deduped
