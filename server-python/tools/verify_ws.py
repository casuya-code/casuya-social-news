"""Live verification: real server + real WS client receives script deltas.

Requires the server running on 127.0.0.1:8000 with API_KEY=test-key.
Reset state first so /news/refresh produces fresh stories.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
import websockets

WS_URL = "ws://127.0.0.1:8000/api/v1/ws?api_key=test-key"
API_URL = "http://127.0.0.1:8000/api/v1/news/refresh"
HEADERS = {"X-API-Key": "test-key"}


async def main() -> None:
    async with websockets.connect(WS_URL) as ws:
        snapshot = await ws.recv()
        print("snapshot:", snapshot[:120], "...")

        async with httpx.AsyncClient() as client:
            r = await client.post(API_URL, headers=HEADERS, timeout=60)
            print("refresh status:", r.status_code, "ingested:", r.json().get("ingested"))

        received = []
        try:
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                received.append(msg)
        except TimeoutError:
            pass

        print(f"received {len(received)} live message(s):")
        for msg in received:
            print(" ", msg[:140])


if __name__ == "__main__":
    asyncio.run(main())
