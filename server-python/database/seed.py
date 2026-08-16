"""Seed database tables from the canonical cast list and admin credentials.

Called once at server startup so that FK constraints on MemoryEvent→characters
are satisfied from the very first ingest cycle, and the admin user exists for
JWT login.
"""

from __future__ import annotations

from config.logging_config import get_logger
from database.engine import SessionLocal
from database.models import Character, User
from nlp.contextualizer import CAST
from security.password import hash_password

_logger = get_logger("database.seed")


async def seed_characters() -> None:
    """Insert canonical cast members if the characters table is empty.

    Uses explicit existence checks so repeated startup calls are idempotent.
    """
    try:
        async with SessionLocal() as session:
            for char in CAST:
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
        _logger.info("seed_characters_ok", count=len(CAST))
    except Exception as exc:  # noqa: BLE001 — Postgres may be down; pipeline survives
        _logger.warning("seed_characters_skipped", error=str(exc))


async def seed_admin_user() -> None:
    """Create the default admin operator if no users exist yet.

    Password comes from settings (admin_password). The user record is only
    created once; subsequent startups are no-ops.
    """
    from config.settings import get_settings

    settings = get_settings()
    try:
        async with SessionLocal() as session:
            from sqlalchemy import select

            result = await session.execute(select(User).limit(1))
            if result.first() is not None:
                return  # users already exist
            session.add(
                User(
                    username=settings.admin_username,
                    password_hash=hash_password(settings.admin_password),
                    is_admin=True,
                )
            )
            await session.commit()
        _logger.info("seed_admin_user_ok", username=settings.admin_username)
    except Exception as exc:  # noqa: BLE001 — Postgres may be down; pipeline survives
        _logger.warning("seed_admin_user_skipped", error=str(exc))
