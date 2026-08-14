"""Tests for storage retention purging (README data-retention rules)."""

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.models import Base, NewsArticle, Script
from maintenance.retention import (
    compress_old_scripts,
    is_expired,
    purge,
    purge_expired_articles,
    run_retention,
    script_audio_dirs,
)


def _make_script_dir(storage: Path, name: str, age_hours: float) -> Path:
    path = storage / name
    path.mkdir(parents=True, exist_ok=True)
    (path / "00.wav").write_bytes(b"\x00" * 100)
    mtime = datetime.now(UTC) - timedelta(hours=age_hours)
    os.utime(path, (mtime.timestamp(), mtime.timestamp()))
    return path


@pytest.fixture
def storage(tmp_path):
    return tmp_path / "storage"


@pytest.fixture
def now():
    return datetime.now(UTC)


@pytest.fixture
async def db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'ret.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


def test_script_audio_dirs_only_matches_script_ids(storage):
    fresh = _make_script_dir(storage, "a" * 32, age_hours=0)
    _make_script_dir(storage, "not-a-script-id", age_hours=0)
    _make_script_dir(storage, "abcd", age_hours=0)
    (storage / "seen_urls.json").write_text("{}", encoding="utf-8")

    found = script_audio_dirs(storage)
    assert found == [fresh]
    assert "seen_urls.json" not in [p.name for p in found]


def test_is_expired_uses_mtime(storage):
    old = _make_script_dir(storage, "b" * 32, age_hours=48)
    new = _make_script_dir(storage, "c" * 32, age_hours=1)
    assert is_expired(old, retention_hours=24) is True
    assert is_expired(new, retention_hours=24) is False


def test_purge_removes_only_expired(storage):
    expired = _make_script_dir(storage, "d" * 32, age_hours=72)
    fresh = _make_script_dir(storage, "e" * 32, age_hours=1)
    (storage / "character_state.json").write_text("{}", encoding="utf-8")

    result = purge(storage_dir=storage, retention_hours=24)

    assert result["purged"] == 1
    assert result["kept"] == 1
    assert result["removed"] == [expired.name]
    assert not expired.exists()
    assert fresh.exists()
    assert (storage / "character_state.json").exists()


def test_purge_dry_run_deletes_nothing(storage):
    expired = _make_script_dir(storage, "f" * 32, age_hours=72)
    result = purge(storage_dir=storage, retention_hours=24, dry_run=True)
    assert result["dry_run"] is True
    assert result["purged"] == 1
    assert expired.exists()  # nothing deleted


def test_purge_respects_custom_retention(storage):
    _make_script_dir(storage, "a" * 32, age_hours=10)
    result = purge(storage_dir=storage, retention_hours=24)
    assert result["purged"] == 0  # 10h < 24h default
    result_strict = purge(storage_dir=storage, retention_hours=6)
    assert result_strict["purged"] == 1


async def test_purge_expired_articles_deletes_old_rows(db, now):
    from database.models import NewsArticle

    fresh = NewsArticle(
        headline="fresh",
        source="src",
        url="https://example.com/fresh",
        published_at=now,
        raw_content="",
        fetched_at=now,
    )
    stale = NewsArticle(
        headline="stale",
        source="src",
        url="https://example.com/stale",
        published_at=now - timedelta(hours=72),
        raw_content="",
        fetched_at=now - timedelta(hours=72),
    )
    db.add_all([fresh, stale])
    await db.commit()

    deleted = await purge_expired_articles(db, retention_hours=48, now=now)
    assert deleted == 1
    remaining = await db.get(NewsArticle, stale.id)
    assert remaining is None
    assert await db.get(NewsArticle, fresh.id) is not None


async def test_compress_old_scripts_keeps_fresh(db, now, tmp_path):
    old = Script(
        id="old-script",
        full_json={"news_ref": {"headline": "habari kuu"}, "characters": [], "lines": []},
        created_at=now - timedelta(hours=48),
    )
    fresh = Script(
        id="fresh-script",
        full_json={"news_ref": {"headline": "mpya"}, "characters": [], "lines": []},
        created_at=now - timedelta(hours=1),
    )
    db.add_all([old, fresh])
    await db.commit()

    result = await compress_old_scripts(db, retention_hours=24, now=now)
    assert result["compressed"] == 1

    refreshed_old = await db.get(Script, old.id)
    assert refreshed_old.summary is not None
    assert refreshed_old.summary.startswith("habari kuu")
    assert refreshed_old.full_json == {}

    refreshed_fresh = await db.get(Script, fresh.id)
    expected_full = {"news_ref": {"headline": "mpya"}, "characters": [], "lines": []}
    assert refreshed_fresh.full_json == expected_full


async def test_run_retention_orchestrates_audio_and_db(db, now, tmp_path):
    storage = tmp_path / "storage"
    storage.mkdir()
    expired_dir = _make_script_dir(storage, "a" * 32, age_hours=72)
    stale_article = NewsArticle(
        headline="stale",
        source="src",
        url="https://example.com/stale2",
        published_at=now - timedelta(hours=72),
        raw_content="",
        fetched_at=now - timedelta(hours=72),
    )
    db.add(stale_article)
    await db.commit()

    result = await run_retention(
        storage_dir=storage,
        audio_hours=24,
        article_hours=48,
        script_hours=24,
        now=now,
        session=db,
    )
    assert result["audio"]["purged"] == 1
    assert result["articles_deleted"] == 1
    assert not expired_dir.exists()
