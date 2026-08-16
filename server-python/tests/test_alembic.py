"""Tests for the alembic migration wiring (upgrade/seed/downgrade)."""

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from alembic.config import Config
from database.models import AppMeta, Character, MemoryEvent, NewsArticle, Script, User, Vote


def _alembic_config(db_url: str) -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("script_location", "alembic")
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def test_upgrade_head_creates_all_tables(tmp_path):
    db_path = tmp_path / "migrate.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    command.upgrade(_alembic_config(db_url), "head")

    async def _assert():
        engine = create_async_engine(db_url)
        try:
            async with engine.connect() as conn:
                rows = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
                names = {r[0] for r in rows if not r[0].startswith("alembic")}
                row = await conn.execute(
                    text("SELECT value FROM app_meta WHERE key='schema_version'")
                )
                stored = row.scalar()
        finally:
            await engine.dispose()

        expected = {
            AppMeta.__tablename__,
            Character.__tablename__,
            MemoryEvent.__tablename__,
            NewsArticle.__tablename__,
            Script.__tablename__,
            User.__tablename__,
            Vote.__tablename__,
        }
        assert expected <= names
        assert stored == "1"  # seeded so check_schema_version() passes

    asyncio.run(_assert())


def test_upgrade_then_downgrade_round_trip(tmp_path):
    db_path = tmp_path / "rt.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    cfg = _alembic_config(db_url)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")

    async def _assert_empty():
        engine = create_async_engine(db_url)
        try:
            async with engine.connect() as conn:
                rows = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
                names = {r[0] for r in rows if not r[0].startswith("alembic")}
        finally:
            await engine.dispose()
        assert names == set()  # downgrade base drops every table

    asyncio.run(_assert_empty())
