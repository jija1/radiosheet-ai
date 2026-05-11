from __future__ import annotations

from app.api.v1.runsheet.schemas import ProgrammeInput, Segment, SegmentType

_OPENING = "opening"
_MIDDLE  = "middle"
_CLOSING = "closing"

# ---------------------------------------------------------------------------
# Templates — six types × three positions (CLAUDE.md Session 5)
# ---------------------------------------------------------------------------

_TEMPLATES: dict[SegmentType, dict[str, str]] = {
    SegmentType.INTRO: {
        _OPENING: (
            "Good day, you're listening to {station_name}. I'm {presenter_name} "
            "and we have a great {duration_minutes} minutes ahead of you. "
            "Stay tuned for music, news, and more."
        ),
        _MIDDLE: (
            "Welcome back to {station_name}. I'm {presenter_name} — "
            "coming up next we have more great content for you."
        ),
        _CLOSING: (
            "You're still with {station_name} and {presenter_name}. "
            "Let's keep this going — plenty more to come."
        ),
    },
    SegmentType.MUSIC: {
        _OPENING: (
            "We're kicking things off with {duration_minutes} minutes of "
            "great music here on {station_name}. Sit back and enjoy."
        ),
        _MIDDLE: (
            "Time to sit back — here's {duration_minutes} minutes of "
            "non-stop music on {station_name}."
        ),
        _CLOSING: (
            "Before we wrap up, here's one final music set for you "
            "on {station_name}. Enjoy."
        ),
    },
    SegmentType.NEWS: {
        _OPENING: "Let's get you up to speed. Here is the news on {station_name}.",
        _MIDDLE: (
            "Time for your {duration_minutes}-minute news update "
            "here on {station_name}."
        ),
        _CLOSING: (
            "And finally, here's a brief news roundup before we close "
            "here on {station_name}."
        ),
    },
    SegmentType.WEATHER: {
        _OPENING: (
            "Let's check in on today's conditions. Here's your "
            "weather update on {station_name}."
        ),
        _MIDDLE: (
            "Here's your {duration_minutes}-minute weather and "
            "traffic update on {station_name}."
        ),
        _CLOSING: (
            "A quick weather check before we wrap up today "
            "on {station_name}."
        ),
    },
    SegmentType.ADVERT: {
        _OPENING: (
            "A quick word from our sponsors — we'll be right back "
            "on {station_name}."
        ),
        _MIDDLE: (
            "Stay with us — back in {duration_minutes} minutes "
            "on {station_name}."
        ),
        _CLOSING: (
            "One last message from our partners before we close "
            "on {station_name}."
        ),
    },
    SegmentType.CLOSE: {
        _OPENING: "That's not applicable for a close segment.",
        _MIDDLE: (
            "That's all from me, {presenter_name}, on {station_name}. "
            "Join us again next time."
        ),
        _CLOSING: (
            "Thank you for listening to {station_name}. "
            "This has been {presenter_name}. Until next time — take care."
        ),
    },
}

_GENERIC = "Segment: {name} — {duration_minutes} minutes."


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_notes(
    segments: list[Segment],
    programme_input: ProgrammeInput,
) -> list[Segment]:
    """
    Return the same segments with presenter_notes populated on every item.
    Position is determined by list index: first = opening, last = closing,
    all others = middle. Types absent from the six-type table get a generic note.
    """
    if not segments:
        return segments

    n = len(segments)
    result: list[Segment] = []

    for i, seg in enumerate(segments):
        if i == 0:
            position = _OPENING
        elif i == n - 1:
            position = _CLOSING
        else:
            position = _MIDDLE

        note = _build_note(seg, programme_input, position)
        result.append(seg.model_copy(update={"presenter_notes": note}))

    return result


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _build_note(seg: Segment, programme: ProgrammeInput, position: str) -> str:
    type_templates = _TEMPLATES.get(seg.type)

    if type_templates is None:
        return _GENERIC.format(name=seg.name, duration_minutes=seg.duration_minutes)

    # Fall back to middle if a position key is somehow missing
    template = type_templates.get(position) or type_templates[_MIDDLE]

    return template.format(
        station_name=programme.station_name,
        presenter_name=programme.presenter_name,
        duration_minutes=seg.duration_minutes,
        name=seg.name,
    )
