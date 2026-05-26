"""Audience growth helpers — patterns that increase listener retention."""
from __future__ import annotations

from app.api.v1.runsheet.schemas import Segment, SegmentType

_LOCAL_MUSIC_KEYWORDS = {"highlife", "local", "ghana", "afro", "twi", "akan", "ewe"}


def local_music_ratio(segments: list[Segment]) -> float:
    """
    Estimate local music ratio from segment names.
    Returns a float 0.0–1.0 where 1.0 = all music is local.
    """
    music_segs = [s for s in segments if s.type == SegmentType.MUSIC]
    if not music_segs:
        return 1.0  # no music → not an issue
    local_count = sum(
        1 for s in music_segs
        if any(kw in s.name.lower() for kw in _LOCAL_MUSIC_KEYWORDS)
    )
    return local_count / len(music_segs)


def has_engagement_type(segments: list[Segment]) -> bool:
    """True if any high-engagement segment (interview, phone-in, vox_pop) is present."""
    return any(
        s.type in {SegmentType.INTERVIEW, SegmentType.PHONE_IN_SEGMENT, SegmentType.VOX_POP}
        for s in segments
    )
