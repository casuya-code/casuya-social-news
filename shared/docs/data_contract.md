# Data Contract — Python ⇄ Godot

This document defines how the Python server and Godot client exchange data.
It reflects the **implemented** behavior (commit `c8d2d58`+), not just the
plan.

## Communication Channels

| Channel | Direction | Protocol | Used For |
|---|---|---|---|
| REST API | Client → Server | HTTPS + JSON | Generate script, synthesize audio, fetch/refresh news, vote, weather |
| WebSocket | Server → Client | WSS + JSON | Live `state_snapshot` on connect + `script_delta` pushes (Feature #27) |

## Authentication

- Every request carries an `X-API-Key` header (see `.env.example` → `API_KEY`).
- WebSocket connects authenticate via `?api_key=` query parameter; a bad key
  closes the socket with code **4401**.
- Operator sessions authenticate with a JWT access token via
  `Authorization: Bearer <token>` instead of the API key (see `/auth/login`).
- No browser origin/CORS is required — this is a native Godot client.
- Failed auth returns envelope with `error_code: "E4001"` (HTTP 401);
  expired JWTs return `"E4002"`.

### JWT Session Flow

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/auth/login` | `{username, password}` (operator creds from settings) → `{access_token, refresh_token, expires_in}` |
| `POST /api/v1/auth/refresh` | Bearer refresh token → new token pair (rotation) |
| `GET /api/v1/auth/me` | Bearer access token → operator claims (`sub`, `token_type`) |

- Access tokens expire after `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (default 24h);
  refresh tokens after `JWT_REFRESH_TOKEN_EXPIRE_DAYS` (default 30d).
- Each token carries a unique `jti` (for rotation/revocation tracking).
- A valid access token works on every `/api/v1` route in place of the API key.

## Rate Limits

Per client IP, per minute (sliding window — see `middleware/rate_limiter.py`):

| Bucket | Limit | Routes |
|---|---|---|
| general | 60/min | everything else |
| voice | 5/min | `/api/v1/scripts/generate-audio` |

Exceeding a budget returns HTTP 429 with `error_code: "E4003"` and a
`Retry-After` header.

## Script Payload

Full schema: `shared/schemas/script_schema.json`

```
{
  "version": "1.0",
  "script_id": "32-hex uuid",
  "news_ref": { "headline", "source", "published_at", "url" },
  "characters": [
    { "id", "name", "voice_id", "mood",
      "mood_value": float, "mood_label": str, "memory": str }
  ],
  "lines": [
    { "index", "character_id", "text", "emotion",
      "overlap": bool, "audio_url": str|null }
  ],
  "metadata": {
    "generated_at", "time_of_day": "asubuhi|mchana|usiku",
    "mood_drift_applied": bool, "characters_delta": int,
    "weather": { "location", "condition", "mood_offset",
                 "time_of_day", "source", "captured_at" }
  }
}
```

- `characters[].mood_value` / `mood_label` / `memory` expose the character's
  live drift state so the client can render mood changes (Features #22/#25).
- `metadata.weather` is populated by the ingestor (Feature #30).
- `metadata.characters_delta` is set on WebSocket broadcasts (Feature #27).

## Story Direction (Community Steering)

`POST /api/v1/scripts/generate` accepts an optional `direction` field, one of:

- `msisimko` (excitement) · `furaha` (joy) · `wasiwasi` (worry) · `utulivu` (calm)

The community's votes resolve a "pulse" direction that automatically tones
the next ingestion batch. See `POST /api/v1/economy/vote`.

## WebSocket Messages

### On connect — `state_snapshot`

```
{ "type": "state_snapshot", "characters": { "char_id": { "memory", "mood" }, ... } }
```

### On each generated story — `script_delta`

```
{
  "type": "script_delta",
  "script_id": "…",
  "headline": "…",
  "time_of_day": "…",
  "characters_delta": [ { "id", "name", "mood", "mood_label", "memory" } ]
}
```

Only characters whose mood/memory actually changed are included — the
client merges them into its local state.

## Endpoints (`/api/v1`)

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/login` | Operator credentials → JWT token pair |
| POST | `/auth/refresh` | Rotate refresh token into a new pair |
| GET | `/auth/me` | Operator claims for the current access token |
| GET | `/health` | Dependency status (db/cache/tts), circuit snapshot, scheduler state |
| POST | `/scripts/generate` | News JSON → script (cache keyed by URL) |
| GET | `/scripts` | List recently generated scripts, newest first (`?limit=`, clamped 1–100); returns `{scripts: [{script_id, headline, direction, created_at, line_count}], count}` |
| GET | `/scripts/{script_id}` | Fetch a previously generated script by id (listen mode); 404 `E3001` if missing |
| POST | `/scripts/generate-audio` | Script → WAV files, returns audio URLs |
| GET | `/news/latest` | Most recent ingested articles |
| POST | `/news/refresh` | Run ingest+generate now; returns scripts |
| POST | `/economy/vote` | `{script_id, client_id, direction}` |
| GET | `/economy/stats/{script_id}` | Vote tally + winning direction |
| GET | `/economy/influence/{client_id}` | Distinct scripts a client steered |
| GET | `/weather?location=…` | Current weather snapshot for a location |
| WS | `/ws?api_key=…` | Live updates (see above) |

## Response Envelope

Every endpoint returns (see `shared/schemas/api_response.json`):

```
{ "success": bool, "status_code": int, "message": str,
  "error_code": str|null, "request_id": str|null, "data": ... }
```

- Success: `success: true`, `error_code: null`, payload in `data`.
- Error: `success: false`, machine-readable `error_code`, `data: null`.

Implemented error codes:

| Code | Meaning |
|---|---|
| `E0000` | Unhandled internal error |
| `E1001` | Invalid input / script generation failed |
| `E1002` | Emotion tagging failed (tag not in shared registry) |
| `E1003` | Script generation timed out (504) |
| `E2001` | TTS provider failure |
| `E2002` | TTS provider quota/budget exhausted |
| `E2003` | Audio file write failed |
| `E3001` | Not found |
| `E3002` | Database unreachable |
| `E3003` | Database migration required (schema version mismatch, 409) |
| `E4001` | Invalid/missing API key or token |
| `E4002` | JWT expired |
| `E4003` | Rate limit exceeded |
| `E5001` | News source unavailable (ingest falls back to mock feed) |
| `E5002` | News source rate limited (ingest falls back to mock feed) |

## Versioning

- Schema version lives in the `version` field of each payload.
- Breaking changes bump the schema version and the API path (`/api/v1/...`).
- Old clients keep working until they migrate to the new version.

## Change Protocol

To change a field:
1. Bump the schema `version`.
2. Add a migration note here (date + change).
3. Update both `shared/schemas/*.json` and the corresponding Pydantic model.
4. Add a regression test on both server and client.

## Migration Log

| Date | Change |
|---|---|
| 2026-08-13 | Initial contract. |
| 2026-08-14 | Added `characters[].mood_value|mood_label|memory`; `metadata.weather` (Feature #30); `direction` input; economy + weather endpoints; `state_snapshot`/`script_delta` WS types; rate-limit headers; implemented error codes. |