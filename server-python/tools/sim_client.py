"""Simulated Godot client — the full loop without a GUI.

Connects to the live server like the Godot client would, then:
  1. Receives the `state_snapshot` of the current cast (memory + mood).
  2. Optionally triggers a refresh so fresh stories flow.
  3. Prints each live `script_delta` story as it's pushed over the WebSocket.
  4. Optionally votes on each story, steering the community pulse.

Usage:
  python tools/sim_client.py                    # connect, trigger refresh, print stories
  python tools/sim_client.py --listen 60        # stay connected 60s for scheduler pushes
  python tools/sim_client.py --vote             # vote on each story as it arrives
  python tools/sim_client.py --client sim-1     # stable client id (influence tracking)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
import websockets

DEFAULT_WS = "ws://127.0.0.1:8000/api/v1/ws?api_key=test-key"
DEFAULT_API = "http://127.0.0.1:8000/api/v1"
DEFAULT_HEADERS = {"X-API-Key": "test-key"}

DIRECTIONS = ("msisimko", "furaha", "wasiwasi", "utulivu")


def _vote_payload(script_id: str, client_id: str) -> dict:
    return {"script_id": script_id, "client_id": client_id, "direction": random.choice(DIRECTIONS)}


async def _vote(client: httpx.AsyncClient, base: str, payload: dict, headers: dict) -> None:
    try:
        r = await client.post(f"{base}/economy/vote", json=payload, headers=headers, timeout=15)
        body = r.json()
        ok = r.status_code == 200 and body.get("success", True)
        print(
            f"  voted {payload['direction']} on {payload['script_id'][:12]}… "
            f"({'ok' if ok else body.get('message', r.status_code)})"
        )
    except httpx.HTTPError as exc:
        print(f"  vote failed: {exc}")


def _print_story(message: dict) -> str:
    """Render one script_delta as a story headline + character changes."""
    lines = [f"[STORY] {message.get('headline', '?')}  (time: {message.get('time_of_day')})"]
    for char in message.get("characters_delta", []):
        mood = char.get("mood_label") or char.get("mood")
        memory = char.get("memory") or "—"
        lines.append(f"  {char.get('name', char.get('id'))}  mood={mood}  memory={memory}")
    return "\n".join(lines)


async def run_sim(
    *,
    ws_url: str = DEFAULT_WS,
    api_base: str = DEFAULT_API,
    headers: dict | None = None,
    listen_seconds: float = 0.0,
    vote: bool = False,
    client_id: str = "sim-client",
    refresh: bool = True,
    max_stories: int = 0,
) -> dict:
    """Run the simulated client session. Returns a small result summary.

    Waits `listen_seconds` for pushes (0 = a short settle after refresh).
    `max_stories` caps how many deltas are printed (0 = unlimited).
    """
    headers = headers or DEFAULT_HEADERS
    results = {"snapshot_characters": 0, "stories_seen": 0, "votes_cast": 0}

    async with websockets.connect(ws_url) as ws:
        snapshot = json.loads(await ws.recv())
        results["snapshot_characters"] = len(snapshot.get("characters", {}))
        print("snapshot characters:", results["snapshot_characters"])
        for char_id, state in list(snapshot.get("characters", {}).items())[:3]:
            print(f"  {char_id}: mood={state.get('mood')} memory={state.get('memory')!r}")

        async with httpx.AsyncClient() as client:
            if refresh:
                try:
                    r = await client.post(f"{api_base}/news/refresh", headers=headers, timeout=60)
                    body = r.json()
                    print(f"refresh: status={r.status_code} ingested={body.get('ingested', '?')}")
                except httpx.HTTPError as exc:
                    print(f"refresh failed: {exc}")

            async def consume() -> None:
                while True:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=0.3)
                    except TimeoutError:
                        break
                    except Exception as exc:  # noqa: BLE001 - WS closed
                        print(f"  ws closed: {exc}")
                        return
                    message = json.loads(raw)
                    if message.get("type") == "script_delta":
                        results["stories_seen"] += 1
                        print(_print_story(message))
                        if vote:
                            payload = _vote_payload(message["script_id"], client_id)
                            await _vote(client, api_base, payload, headers)
                            results["votes_cast"] += 1
                            if max_stories and results["stories_seen"] >= max_stories:
                                return

            await consume()

            # Keep listening for scheduler-driven pushes if requested.
            if listen_seconds > 0:

                async def listen() -> None:
                    while True:
                        try:
                            raw = await asyncio.wait_for(ws.recv(), timeout=listen_seconds)
                        except TimeoutError:
                            return
                        except Exception as exc:  # noqa: BLE001
                            print(f"  ws closed: {exc}")
                            return
                        message = json.loads(raw)
                        if message.get("type") == "script_delta":
                            results["stories_seen"] += 1
                            print(_print_story(message))
                            if vote:
                                payload = _vote_payload(message["script_id"], client_id)
                                await _vote(client, api_base, payload, headers)
                                results["votes_cast"] += 1
                            if max_stories and results["stories_seen"] >= max_stories:
                                return

                await listen()

    print(f"\ndone: {results}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulated Godot client demo")
    parser.add_argument("--ws", default=DEFAULT_WS, help="WebSocket URL")
    parser.add_argument("--api", default=DEFAULT_API, help="REST API base URL")
    parser.add_argument("--api-key", default="test-key", help="API key")
    parser.add_argument(
        "--listen", type=float, default=0.0, help="seconds to keep listening after refresh"
    )
    parser.add_argument("--vote", action="store_true", help="vote on each story (steers the pulse)")
    parser.add_argument("--client", default="sim-client", help="stable client id")
    parser.add_argument(
        "--max-stories", type=int, default=0, help="stop after N stories (0 = unlimited)"
    )
    parser.add_argument("--no-refresh", action="store_true", help="don't trigger /news/refresh")
    args = parser.parse_args()

    asyncio.run(
        run_sim(
            ws_url=args.ws,
            api_base=args.api,
            headers={"X-API-Key": args.api_key},
            listen_seconds=args.listen,
            vote=args.vote,
            client_id=args.client,
            refresh=not args.no_refresh,
            max_stories=args.max_stories,
        )
    )


if __name__ == "__main__":
    main()
