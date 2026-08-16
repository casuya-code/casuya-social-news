"""WebSocket server — live updates to connected clients (Feature #27).

Clients connect to `/api/v1/ws?api_key=<key>`. On success they receive a
`state_snapshot` of the current cast. When new stories generate, only the
delta (changed characters) is broadcast, keeping payloads tiny on mobile.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.delta_compressor import build_script_delta
from config.logging_config import get_logger
from config.settings import get_settings
from monitoring.metrics import WS_CONNECTIONS, WS_MESSAGES_SENT
from nlp.character_state import load_states

_logger = get_logger("api.ws")
_settings = get_settings()

router = APIRouter()


class ConnectionManager:
    """Tracks live WebSocket connections and fans out messages."""

    def __init__(self) -> None:
        self._active: set[WebSocket] = set()

    @property
    def count(self) -> int:
        return len(self._active)

    async def connect(self, ws: WebSocket) -> None:
        if ws.client_state.name == "CONNECTING":
            await ws.accept()
        self._active.add(ws)
        WS_CONNECTIONS.set(self.count)
        _logger.info("ws_connected", clients=self.count)

    def disconnect(self, ws: WebSocket) -> None:
        self._active.discard(ws)
        WS_CONNECTIONS.set(self.count)
        _logger.info("ws_disconnected", clients=self.count)

    async def send(self, ws: WebSocket, message: dict) -> None:
        await ws.send_text(json.dumps(message))
        WS_MESSAGES_SENT.labels(message_type=message.get("type", "unknown")).inc()

    async def broadcast(self, message: dict) -> None:
        payload = json.dumps(message)
        for ws in list(self._active):
            try:
                await ws.send_text(payload)
                WS_MESSAGES_SENT.labels(message_type=message.get("type", "unknown")).inc()
            except Exception:  # noqa: BLE001 - drop dead connections
                self.disconnect(ws)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, api_key: str = "") -> None:
    """Live update channel. Auth via query param ``api_key``."""
    if api_key != _settings.api_key:
        _logger.warning("ws_auth_failed", reason="invalid_key")
        await ws.close(code=4401)
        return

    await manager.connect(ws)
    await manager.send(ws, {"type": "state_snapshot", "characters": load_states()})

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


async def broadcast_script(script: dict, prev_states: dict[str, dict]) -> None:
    """Compress and push a script's character changes to live clients."""
    if manager.count == 0:
        return
    try:
        delta = build_script_delta(script, prev_states)
        await manager.broadcast(delta)
    except Exception:  # noqa: BLE001 - never let a push break ingestion
        _logger.warning("ws_broadcast_failed")
