"""Feature #34: product placement — sponsored sign-off lines in scripts.

Sponsor brands are drawn from a local catalog; when a script is selected for
placement, a sponsor sign-off line is appended after the closing line and the
brand is recorded under `metadata.product_placement` for UI badging.

Placement uses its own RNG seeded by the news URL + cast state (NOT the
community direction), so the number of lines is stable across directions —
which keeps script structure deterministic for the client.
"""

from __future__ import annotations

import random
from typing import Any

# Local sponsor catalog: brand + a natural-sounding Swahili mention.
_PLACEMENTS = [
    {
        "brand": "Maji Safi",
        "tagline": "Maji Safi ni chaguo la familia",
        "emotion": "anaongea_kwa_utulivu",
    },
    {
        "brand": "Shujaa Energy",
        "tagline": "Nguvu ya Shujaa huendeleza hadi jioni",
        "emotion": "anajigamba",
    },
    {
        "brand": "Bima Njema",
        "tagline": "Bima Njema inakulinda wakati wowote",
        "emotion": "anahofia",
    },
    {
        "brand": "Kilimo Plus",
        "tagline": "Kilimo Plus chachu huzaa zaidi",
        "emotion": "anapiga_kelele",
    },
    {
        "brand": "Simu Bora",
        "tagline": "Simu Bora inaunganisha mwananchi na dunia",
        "emotion": "anashangaa",
    },
]

_PLACEMENT_CHANCE = 0.40  # share of scripts that carry a sponsor sign-off


def _placement_rng(news_url: str, cast_state: dict[str, dict] | None) -> random.Random:
    """Direction-independent RNG so placement never changes line count per scene."""
    return random.Random(f"placement:{news_url}:{cast_state or {}}")


def _signoff_line(
    brand: dict[str, str],
    index: int,
    speaker: str,
) -> dict[str, Any]:
    return {
        "index": index,
        "character_id": speaker,
        "text": f"{brand['tagline']}. {brand['brand']} — mwenza wako leo.",
        "emotion": brand["emotion"],
        "overlap": False,
    }


def select_placement(
    news_url: str,
    cast_state: dict[str, dict] | None,
    speaker: str,
    next_index: int,
    catalog: list[dict[str, str]] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
    """Decide whether this script gets a sponsor sign-off line.

    Returns (line, metadata_badge). Metadata badge holds brand + tagline for
    `metadata.product_placement`. Deterministic per (url, cast_state).
    """
    rng = _placement_rng(news_url, cast_state)
    if rng.random() >= _PLACEMENT_CHANCE:
        return None, None
    brand = rng.choice(catalog or _PLACEMENTS)
    line = _signoff_line(brand, next_index, speaker)
    badge = {"brand": brand["brand"], "tagline": brand["tagline"]}
    return line, badge
