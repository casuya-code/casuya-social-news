"""Tests for WebSocket live delta updates (Feature #27)."""

import json

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from api.delta_compressor import build_character_delta, build_script_delta
from api.websocket_server import ConnectionManager, manager
from main import app
from nlp.contextualizer import contextualize

client = TestClient(app)

SAMPLE_NEWS = {
    "headline": "Mvua kubwa yameleta mafuriko mkoani Dar es Salaam",
    "source": "Tanzania News",
    "url": "https://example.com/mafuriko-dar",
    "published_at": "2026-08-13T10:00:00Z",
}


class FakeSocket:
    """Minimal WebSocket stand-in to exercise ConnectionManager.broadcast."""

    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_text(self, text: str) -> None:
        self.sent.append(json.loads(text))


@pytest.mark.asyncio
async def test_manager_broadcast_fans_out():
    cm = ConnectionManager()
    socket = FakeSocket()
    cm._active.add(socket)
    await cm.broadcast({"type": "script_delta", "script_id": "abc"})
    assert socket.sent == [{"type": "script_delta", "script_id": "abc"}]
    cm.disconnect(socket)
    assert cm.count == 0


@pytest.mark.asyncio
async def test_broadcast_script_noop_without_clients():
    # No connections → broadcast must not raise and must not touch manager.
    before = manager.count
    await manager.broadcast({"type": "script_delta"})
    assert manager.count == before


def test_ws_auth_success_sends_snapshot():
    with client.websocket_connect("/api/v1/ws?api_key=test-key") as ws:
        message = ws.receive_json()
        assert message["type"] == "state_snapshot"
        assert "characters" in message


def test_ws_auth_failure_closes():
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/api/v1/ws?api_key=wrong-key"):
            pass  # connection should be refused immediately
    assert exc_info.value.code == 4401


def test_build_character_delta_only_changed():
    characters = [
        {"id": "char_a", "name": "A", "mood_value": 0.5, "mood_label": "anafuraha", "memory": "x"},
        {
            "id": "char_b",
            "name": "B",
            "mood_value": 0.0,
            "mood_label": "hali ya kawaida",
            "memory": "",
        },
    ]
    prev = {"char_a": {"mood": 0.0, "memory": ""}, "char_b": {"mood": 0.0, "memory": ""}}
    deltas = build_character_delta(characters, prev)
    ids = [d["id"] for d in deltas]
    assert ids == ["char_a"]  # only char_a changed


def test_build_character_delta_no_changes():
    characters = [
        {
            "id": "char_a",
            "name": "A",
            "mood_value": 0.2,
            "mood_label": "ana msisimko",
            "memory": "habari",
        },
    ]
    prev = {"char_a": {"mood": 0.2, "memory": "habari"}}
    assert build_character_delta(characters, prev) == []


def test_build_script_delta_shape():
    script = contextualize(SAMPLE_NEWS, {"char_a": {"memory": "", "mood": 0.0}})
    delta = build_script_delta(script, {"char_a": {"memory": "", "mood": 0.0}})
    assert delta["type"] == "script_delta"
    assert delta["script_id"] == script["script_id"]
    assert "headline" in delta
    assert "characters_delta" in delta
    assert script["metadata"]["characters_delta"] == len(delta["characters_delta"])
