"""In-process smoke test of the MVP endpoints (no live server needed)."""

import asyncio

import httpx

from main import app


async def main() -> None:
    transport = httpx.ASGITransport(app=app)
    headers = {"X-API-Key": "test-key"}

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Root
        r = await client.get("/")
        print("root:", r.status_code, r.json())

        # 2. Unauthorized (no key)
        r = await client.get("/api/v1/health")
        print("health no-key:", r.status_code, r.json())

        # 3. Generate script
        r = await client.post(
            "/api/v1/scripts/generate",
            json={
                "headline": "Mvua kubwa yameleta mafuriko mkoani Dar es Salaam",
                "source": "Tanzania News",
                "url": "https://example.com/mafuriko-dar",
            },
            headers=headers,
        )
        print("generate:", r.status_code)
        body = r.json()
        script = body["script"]
        print("  script_id:", script["script_id"])
        print("  lines:", len(script["lines"]))
        for line in script["lines"]:
            print(
                "   ",
                line["index"],
                line["character_id"],
                "->",
                line["emotion"],
                "|",
                line["text"][:50],
            )

        # 4. Generate audio (mock provider)
        r = await client.post(
            "/api/v1/scripts/generate-audio",
            json={"script": script},
            headers=headers,
        )
        print("generate-audio:", r.status_code)
        body = r.json()
        for line in body["lines"]:
            print("   audio_url:", line["audio_url"])

        # 5. Health (DB will be 'down' but endpoint should respond)
        r = await client.get("/api/v1/health", headers=headers)
        print("health with key:", r.status_code, r.json())


if __name__ == "__main__":
    asyncio.run(main())
