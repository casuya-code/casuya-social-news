"""Contextualizer (Feature #24): news article → dramatic script.

MVP uses a deterministic template generator so the system works without
an LLM API key. It weaves in character memory + mood drift (Features #22,
#25) so stories feel continuous. The interface mirrors what a real
LLM-backed version will look like, so swapping in `openai` later is a
drop-in change.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from nlp.emotion_tagger import tag_line
from nlp.memory import mood_label
from nlp.product_placement import select_placement

_CAST: list[dict[str, str]] = [
    {"id": "char_bibi_mkwe", "name": "Bibi Mkwe", "voice_id": "mock_bibi", "mood": "uchangamfu"},
    {"id": "char_mjomba", "name": "Mjomba Juma", "voice_id": "mock_mjomba", "mood": "hasira"},
    {"id": "char_rafiki", "name": "Rafiki Neema", "voice_id": "mock_neema", "mood": "msisimko"},
]

_OPENINGS = [
    "Hujasikia? Mambo yameendelea leo!",
    "Wewe, leo kuna habari kubwa!",
    "Ngoja nikuambie kilichotokea...",
]

_MEMORY_OPENINGS = [
    "Kumbuka tulichokizungumzia jana... sasa inaendelea!",
    "Hii ni mwendelezo wa habari tuliyoiona hapo awali.",
    "Unakumbuka tulivyozungumza? Leo imekuwa kubwa zaidi.",
]

_REACTIONS_NEUTRAL = [
    "Haiwezekani! Kweli ndivyo ilivyo?",
    "Nashangaa sana kusikia hivyo.",
    "Mh... hii inabadilisha mambo mengi.",
    "Lakini sasa, hii ni hatari kweli.",
]

_REACTIONS_WORRIED = [
    "Hii inatia wasiwasi sana. Tunaweza kufanya nini?",
    "Sidhani kama tutajisikia vizuri na habari kama hii.",
    "Mh... wakati mgumu unakuja. Tunahitaji kuwa makini.",
]

_REACTIONS_UPBEAT = [
    "Hii ni nzuri sana! Kila mtu akusanye habari hii!",
    "Nimefurahi sana! Tumekuwa tukingojea hii kwa muda.",
    "Kesho watu wote watakuwa wakizungumza kuhusu hii!",
]

_CLOSINGS = [
    "Basi, tunaendelea kuona mambo yatakavyokuwa.",
    "Tunafuatilia hadithi hii kwa makini.",
    "Na ndivyo ilivyokuwa leo, tusubiri kesho.",
]

# Direction-tuned closings (Feature #35): the community's chosen direction
# shapes how the scene resolves.
_CLOSINGS_BY_DIRECTION = {
    "msisimko": [
        "Na kitu kinachofuata kinaweza kuwa kubwa! Subiri tu.",
        "Msisimko umezidi! Tutakuambia kinachotokea baadaye.",
        "Hii ndiyo mwanzo tu wa mambo makubwa yanayokuja!",
    ],
    "furaha": [
        "Hii inaleta matumaini makubwa kwa siku zijazo!",
        "Tunaweza kufurahi leo; habari nzuri imefika!",
        "Ni siku njema! Tumefurahishwa na mwendo huu.",
    ],
    "wasiwasi": [
        "Tunahitaji kuwa makini sana; mambo bado yanaendelea.",
        "Wasiwasi unaongezeka; tutafuatilia kwa karibu.",
        "Huu ni wakati wa kujiandaa kwa yale yanayokuja.",
    ],
    "utulivu": [
        "Basi, tulia na tusubiri maelezo zaidi.",
        "Tunachukua muda kuangalia mambo kwa utulivu.",
        "Hakuna haraka; tukusanye ukweli kwanza.",
    ],
}


def _truncate(headline: str, limit: int = 40) -> str:
    """Chop a headline down for use inside dialogue."""
    return headline if len(headline) <= limit else headline[: limit - 1] + "…"


# Feature #1: narrative prompts — methali (proverbs) woven into dialogue.
_PROVERBS = [
    "Haraka haraka haina baraka.",
    "Mvumilivu hula mbivu.",
    "Kidole kimoja hakivunji chawa.",
    "Mwacha mila ni mtumwa.",
    "Polepole ndiyo mwendo.",
    "Asiyekujua hakuthamini.",
    "Mtaka yote hukosa yote.",
    "Haba na haba hujaza kibaba.",
]

# Feature #26: slang dictionary — lightweight urban Swahili layer.
_SLANG = {
    "opening": ["Mambo!", "Vipi, kijana?", "Mkuu, unasikia?", "Jambo! Usikilize hii."],
    "filler": ["mpaka nini?", "basi na basi.", "sasa hivi tu.", "niliyaona mato!"],
}

_OPENINGS = [
    "Hujasikia? Mambo yameendelea leo!",
    "Wewe, leo kuna habari kubwa!",
    "Ngoja nikuambie kilichotokea...",
]

_SLANG_OPENINGS = [
    "Mkuu, kuna jambo la moto!",
    "Mambo! Habari kubwa imefika leo!",
    "Ngoja nikwambie, hii ni kubwa sana!",
]


def _reaction_pool(mood: float) -> list[str]:
    """Pick a reaction set tuned to a character's current mood."""
    if mood <= -0.15:
        return _REACTIONS_WORRIED
    if mood >= 0.15:
        return _REACTIONS_UPBEAT
    return _REACTIONS_NEUTRAL


def _carryover_emotion(mood: float, rng: random.Random) -> str:
    """Feature #5: emotion carried over from a character's current mood."""
    if mood <= -0.4:
        return rng.choice(["anakasirika", "anahofia", "anasikitika"])
    if mood >= 0.4:
        return rng.choice(["anajigamba", "anashangaa", "anacheka_kwa_dharau"])
    return tag_line(2)


def build_mock_script(
    news: dict[str, Any],
    cast_state: dict[str, dict] | None = None,
    direction: str = "utulivu",
) -> dict[str, Any]:
    """Create a deterministic script, weaving in memory, mood, and direction."""
    headline = _truncate(news.get("headline", "Habari za leo"))
    rng = random.Random(news.get("url", "casuya") + str(cast_state or {}) + direction)
    cast_state = cast_state or {}

    cast = _CAST[:]
    rng.shuffle(cast)
    cast = cast[:2]  # two speakers per scene for the MVP

    speaker_a = cast[0]["id"]
    speaker_b = cast[1]["id"]
    state_a = cast_state.get(speaker_a, {"memory": "", "mood": 0.0})
    state_b = cast_state.get(speaker_b, {"memory": "", "mood": 0.0})

    # Feature #26: weave slang into the opening.
    if rng.random() < 0.4:
        opening = rng.choice(_SLANG_OPENINGS)
        opening_line = f"{opening} {headline}."
    elif state_a.get("memory"):
        opening = rng.choice(_MEMORY_OPENINGS)
        opening_line = f"{opening} {headline}."
    else:
        opening = rng.choice(_OPENINGS)
        opening_line = f"{opening} {headline}."

    reaction = rng.choice(_reaction_pool(state_b.get("mood", 0.0)))
    direction_pool = _CLOSINGS_BY_DIRECTION.get(direction, _CLOSINGS)
    closing = rng.choice(direction_pool)

    # Feature #1: sometimes resolve with a methali (proverb) for flavor.
    if rng.random() < 0.35:
        closing = f"{closing} {rng.choice(_PROVERBS)}"

    # Feature #5: the closing line carries the speaker's current emotion.
    closing_emotion = _carryover_emotion(state_a.get("mood", 0.0), rng)

    # Feature #6: overlap cues — a heated scene lets lines talk over each other.
    heat = abs(state_a.get("mood", 0.0)) + abs(state_b.get("mood", 0.0))
    overlap_reaction = heat >= 0.4 and rng.random() < 0.6
    overlap_closing = heat >= 0.4 and rng.random() < 0.3

    lines = [
        {
            "index": 0,
            "character_id": speaker_a,
            "text": opening_line,
            "emotion": tag_line(0),
            "overlap": False,
        },
        {
            "index": 1,
            "character_id": speaker_b,
            "text": reaction,
            "emotion": tag_line(1),
            "overlap": overlap_reaction,
        },
        {
            "index": 2,
            "character_id": speaker_a,
            "text": closing,
            "emotion": closing_emotion,
            "overlap": overlap_closing,
        },
    ]

    # Feature #34: append a sponsor sign-off line after the closing.
    placement_line, placement_badge = select_placement(
        news_url=news.get("url", ""),
        cast_state=cast_state,
        speaker=speaker_a,
        next_index=len(lines),
    )
    if placement_line is not None:
        lines.append(placement_line)

    # Expose current mood + memory to the client so the UI can show drift.
    for i, character in enumerate(cast):
        character = dict(character)
        character["mood_value"] = cast_state.get(character["id"], {}).get("mood", 0.0)
        character["mood_label"] = mood_label(character["mood_value"])
        character["memory"] = cast_state.get(character["id"], {}).get("memory", "")
        cast[i] = character

    return {
        "version": "1.0",
        "script_id": uuid4().hex,
        "news_ref": {
            "headline": news.get("headline", ""),
            "source": news.get("source", "unknown"),
            "published_at": news.get("published_at", datetime.now(UTC).isoformat()),
            "url": news.get("url", ""),
        },
        "characters": cast,
        "lines": lines,
        "metadata": {
            "generated_at": datetime.now(UTC).isoformat(),
            "time_of_day": "mchana",
            "mood_drift_applied": bool(cast_state),
            "characters_delta": 0,
            **({"product_placement": placement_badge} if placement_badge else {}),
        },
    }


def contextualize(
    news: dict[str, Any],
    cast_state: dict[str, dict] | None = None,
    direction: str = "utulivu",
) -> dict[str, Any]:
    """Entry point: news → script. Swap this for an LLM call later."""
    return build_mock_script(news, cast_state, direction)
