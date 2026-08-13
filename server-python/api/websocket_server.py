"""WebSocket server — live updates to connected clients (Feature #27).

Clients connect to `/api/v1/ws?api_key=...`. On connect they receive a
`state_snapshot` of the current cast. When new stories generate, only the
delta (changed characters) is broadcast, keeping payloads tiny on mobile.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.delta_compressor import build_script_delta
from config.logging_config import get_logger
from config.settings import get_settings
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
        await ws.accept()
        self._active.add(ws)
        _logger.info("ws_connected", clients=self.count)

    def disconnect(self, ws: WebSocket) -> None:
        self._active.discard(ws)
        _logger.info("ws_disconnected", clients=self.count)

    async def send(self, ws: WebSocket, message: dict) -> None:
        await ws.send_text(json.dumps(message))

    async def broadcast(self, message: dict) -> None:
        payload = json.dumps(message)
        for ws in list(self._active):
            try:
                await ws.send_text(payload)
            except Exception:  # noqa: BLE001 - drop dead connections
                self.disconnect(ws)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, api_key: str = "") -> None:
    """Live update channel. Auth via `?api_key=` query parameter."""
    if api_key != _settings.api_key:
        _logger.warning("ws_auth_failed")
        await ws.close(code=4401)
        return

    await manager.connect(ws)
    # Fresh clients start with the full current cast state (memory + mood).
    await manager.send(ws, {"type": "state_snapshot", "characters": load_states()})

    try:
        while True:
            # We ignore client→server traffic; the channel is server-push.
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
