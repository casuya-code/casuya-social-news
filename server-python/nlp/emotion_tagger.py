"""Emotion tagger (Feature #2): assigns [anacheka_kwa_dharau]-style tags to lines."""

from __future__ import annotations

import random

_TAGS = [
    "anaongea_kwa_huzuni",
    "anacheka_kwa_dharau",
    "anapiga_kelele",
    "anaongea_kwa_utulivu",
    "anashangaa",
    "anafikiria",
    "anakasirika",
    "anahofia",
    "anasikitika",
    "anajigamba",
    "anadhihaki",
]

_INDEX_BASED = {
    0: "anashangaa",  # opening line — surprise/intro
    1: "anafikiria",  # reaction line — thinking
    2: "anaongea_kwa_utulivu",  # closing — calm resolution
}


def tag_line(index: int, rng: random.Random | None = None) -> str:
    """Return an emotion tag for a line at the given index.

    Opening/reaction/closing lines get deterministic tags; any other line
    picks randomly so scenes vary without an LLM.
    """
    if index in _INDEX_BASED:
        return _INDEX_BASED[index]
    rng = rng or random
    return rng.choice(_TAGS)
