"""Tests for the file-backed script store (listen-mode persistence)."""

import json
import uuid

import pytest

from storage import script_store as store
from storage.script_store import load_script, save_script


@pytest.fixture(autouse=True)
def _use_tmp_storage(tmp_path, monkeypatch):
    settings = type("Settings", (), {"storage_dir": tmp_path})()
    monkeypatch.setattr(store, "_settings", settings)


def test_save_and_load_roundtrip():
    script = {
        "script_id": uuid.uuid4().hex,
        "version": "1.0",
        "news_ref": {"headline": "Habari"},
        "lines": [],
    }
    assert save_script(script) is True
    loaded = load_script(script["script_id"])
    assert loaded is not None
    assert loaded["script_id"] == script["script_id"]
    assert loaded["news_ref"]["headline"] == "Habari"


def test_load_missing_returns_none():
    assert load_script("nope") is None


def test_save_requires_script_id():
    assert save_script({"version": "1.0"}) is False


def test_save_script_mismatched_id_returns_none():
    script = {"script_id": uuid.uuid4().hex, "version": "1.0", "lines": []}
    save_script(script)
    # Corrupt the id field to simulate a tampered file.
    path = store.script_path(script["script_id"])
    path.write_text(json.dumps({**script, "script_id": "other"}), encoding="utf-8")
    assert load_script(script["script_id"]) is None
