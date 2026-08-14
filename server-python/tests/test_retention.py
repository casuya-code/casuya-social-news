"""Tests for storage retention purging (README data-retention rules)."""

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from maintenance.retention import is_expired, purge, script_audio_dirs


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
