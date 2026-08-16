"""Seed database tables from the canonical cast list.

Called once at server startup so that FK constraints on MemoryEvent→characters
are satisfied from the very first ingest cycle.
"""

from __future__ import annotations

from config.logging_config import get_logger
from database.engine import SessionLocal
from database.models import Character
from nlp.contextualizer import _CAST

_logger = get_logger("database.seed")


async def seed_characters() -> None:
    """Insert canonical cast members if the characters table is empty.

    Uses ``INSERT ... ON CONFLICT DO NOTHING`` semantics via SQLAlchemy
    ``merge`` so repeated startup calls are idempotent.
    """
    try:
        async with SessionLocal() as session:
            for char in _CAST:
                existing = await session.get(Character, char["id"])
                if existing is None:
                    session.add(
                        Character(
                            id=char["id"],
                            name=char["name"],
                            voice_id=char["voice_id"],
                            mood_base=char.get("mood", "utulivu"),
                        )
                    )
            await session.commit()
        _logger.info("seed_characters_ok", count=len(_CAST))
    except Exception as exc:  # noqa: BLE001 — Postgres may be down; pipeline survives
        _logger.warning("seed_characters_skipped", error=str(exc))
