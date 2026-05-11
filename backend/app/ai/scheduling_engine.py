from __future__ import annotations

import uuid

from app.api.v1.runsheet.schemas import (
    ProgrammeInput,
    ProgrammeType,
    Segment,
    SegmentType,
    TalkMusicPreference,
)

# ---------------------------------------------------------------------------
# Colour map — exact values from CLAUDE.md
# ---------------------------------------------------------------------------

SEGMENT_COLOURS: dict[SegmentType, str] = {
    SegmentType.MUSIC:      "#22c55e",
    SegmentType.TALK:       "#3b82f6",
    SegmentType.ADVERT:     "#f59e0b",
    SegmentType.NEWS:       "#8b5cf6",
    SegmentType.STATION_ID: "#06b6d4",
    SegmentType.WEATHER:    "#10b981",
    SegmentType.CLOSE:      "#6b7280",
    SegmentType.INTRO:      "#3b82f6",
}

# ---------------------------------------------------------------------------
# Stage 1: Programme templates — proportional time allocation
# ---------------------------------------------------------------------------

_TemplateDict = dict[str, float]

TEMPLATES: dict[ProgrammeType, _TemplateDict] = {
    ProgrammeType.MORNING_SHOW: {"music": 0.45, "talk": 0.30, "news": 0.10, "advert": 0.15},
    ProgrammeType.DRIVE_TIME:   {"music": 0.40, "talk": 0.35, "news": 0.10, "advert": 0.15},
    ProgrammeType.NEWS_HOUR:    {"music": 0.10, "talk": 0.30, "news": 0.50, "advert": 0.10},
    ProgrammeType.MUSIC_ONLY:   {"music": 0.75, "talk": 0.05, "news": 0.00, "advert": 0.20},
}

# Minutes reserved for mandatory bookend segments (intro + station_id + close)
_MANDATORY_OVERHEAD = 6

# talk_music_preference shifts music ratio by this amount (talk shifts inversely)
_PREFERENCE_SHIFT: dict[TalkMusicPreference, float] = {
    TalkMusicPreference.HEAVY_MUSIC: +0.15,
    TalkMusicPreference.BALANCED:     0.00,
    TalkMusicPreference.TALK_HEAVY:  -0.15,
}

# Default chunk sizes (minutes) per segment type
_CHUNK_SIZE: dict[str, int] = {
    "music": 4,
    "talk":  4,
    "news":  5,
    "advert": 3,
}

_Chunk = tuple[SegmentType, str, int]  # (type, name, duration_minutes)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate(programme: ProgrammeInput) -> list[Segment]:
    """
    Five-stage pipeline:
      1. Load template proportions for programme_type
      2. Reserve time for fixed segments supplied by the caller
      3. Distribute remaining content time by talk_music_preference
      4. Build advert blocks respecting max_advert_blocks_per_hour
      5. Final layout pass — assign sequential HH:MM times, enforce budget
    """

    # ------------------------------------------------------------------
    # Stage 1: template
    # ------------------------------------------------------------------
    template = TEMPLATES[programme.programme_type]
    total = programme.total_duration_minutes

    # ------------------------------------------------------------------
    # Stage 2: account for caller-supplied fixed segments
    # ------------------------------------------------------------------
    fixed_total = sum(fs.duration_minutes for fs in programme.fixed_segments)

    # ------------------------------------------------------------------
    # Stage 3: distribute remaining content time
    # ------------------------------------------------------------------
    available = max(0, total - fixed_total - _MANDATORY_OVERHEAD)

    advert_budget = int(total * template["advert"])
    content_budget = max(0, available - advert_budget)

    # Apply talk_music_preference to music/talk split
    shift = _PREFERENCE_SHIFT[programme.talk_music_preference]
    raw_music = max(0.0, template["music"] + shift)
    raw_talk  = max(0.0, template["talk"]  - shift)
    raw_news  = template["news"]

    # Normalise the three content ratios so they sum to 1
    ratio_sum = raw_music + raw_talk + raw_news
    if ratio_sum > 0:
        r_music = raw_music / ratio_sum
        r_talk  = raw_talk  / ratio_sum
        r_news  = raw_news  / ratio_sum
    else:
        r_music, r_talk, r_news = 1.0, 0.0, 0.0

    news_mins  = int(content_budget * r_news)
    music_mins = int(content_budget * r_music)
    talk_mins  = content_budget - news_mins - music_mins

    # Build content chunks (type, display-name, duration)
    content_chunks: list[_Chunk] = []
    content_chunks.extend(_make_chunks(SegmentType.MUSIC, "Music",        music_mins, _CHUNK_SIZE["music"]))
    content_chunks.extend(_make_chunks(SegmentType.TALK,  "Talk Segment", talk_mins,  _CHUNK_SIZE["talk"]))
    if news_mins > 0:
        content_chunks.extend(_make_chunks(SegmentType.NEWS, "News",      news_mins,  _CHUNK_SIZE["news"]))

    # Append caller-supplied fixed segments to the content pool
    for fs in programme.fixed_segments:
        content_chunks.append((fs.type, fs.name, fs.duration_minutes))

    # ------------------------------------------------------------------
    # Stage 4: advert blocks
    # ------------------------------------------------------------------
    hours = max(total / 60.0, 0.25)
    max_blocks = max(1, int(programme.max_advert_blocks_per_hour * hours))
    if advert_budget >= 2:
        block_dur = max(2, advert_budget // max_blocks)
        advert_chunks = _make_chunks(
            SegmentType.ADVERT, "Advert Break", advert_budget, block_dur
        )
    else:
        advert_chunks = []

    # Interleave advert blocks evenly through content
    ordered = _interleave(content_chunks, advert_chunks)

    # ------------------------------------------------------------------
    # Stage 5: final layout — assign sequential HH:MM times
    # ------------------------------------------------------------------
    cursor = _hhmm_to_minutes(programme.start_time)
    start  = cursor
    result: list[Segment] = []

    # Mandatory opening: intro (2 min)
    result.append(_build(f"Programme Intro", SegmentType.INTRO, 2, cursor))
    cursor += 2

    # Mandatory: station ID within the first 15 minutes (satisfies C003)
    result.append(_build(f"{programme.station_name} Station ID", SegmentType.STATION_ID, 2, cursor))
    cursor += 2

    # Main content — enforce total budget, reserve 2 min for close
    for seg_type, name, duration in ordered:
        if duration <= 0:
            continue
        elapsed   = cursor - start
        remaining = total - elapsed - 2          # 2 for close
        if remaining <= 0:
            break
        duration = min(duration, remaining)
        result.append(_build(name, seg_type, duration, cursor))
        cursor += duration

    # Mandatory close (2 min) — place if any budget remains
    elapsed = cursor - start
    if elapsed < total:
        result.append(_build("Programme Close", SegmentType.CLOSE, 2, cursor))

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_chunks(seg_type: SegmentType, base_name: str, budget: int, chunk: int) -> list[_Chunk]:
    """Split `budget` minutes into chunks of at most `chunk` minutes."""
    if budget <= 0:
        return []
    chunks: list[_Chunk] = []
    remaining = budget
    i = 1
    while remaining > 0:
        dur = min(chunk, remaining)
        label = f"{base_name} {i}" if budget > chunk else base_name
        chunks.append((seg_type, label, dur))
        remaining -= dur
        i += 1
    return chunks


def _interleave(content: list[_Chunk], adverts: list[_Chunk]) -> list[_Chunk]:
    """Insert one advert block after every N content segments, evenly spaced."""
    if not adverts:
        return list(content)
    if not content:
        return list(adverts)

    step = max(1, len(content) // len(adverts))
    result: list[_Chunk] = []
    advert_it = iter(adverts)

    for i, item in enumerate(content):
        result.append(item)
        if (i + 1) % step == 0:
            try:
                result.append(next(advert_it))
            except StopIteration:
                pass

    for leftover in advert_it:
        result.append(leftover)

    return result


def _build(name: str, seg_type: SegmentType, duration: int, start_mins: int) -> Segment:
    end_mins = start_mins + duration
    return Segment(
        id=str(uuid.uuid4()),
        name=name,
        type=seg_type,
        start_time=_minutes_to_hhmm(start_mins),
        end_time=_minutes_to_hhmm(end_mins),
        duration_minutes=duration,
        colour_hex=SEGMENT_COLOURS[seg_type],
        presenter_notes="",
    )


def _hhmm_to_minutes(time_str: str) -> int:
    h, m = time_str.split(":")
    return int(h) * 60 + int(m)


def _minutes_to_hhmm(minutes: int) -> str:
    minutes = minutes % (24 * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"
