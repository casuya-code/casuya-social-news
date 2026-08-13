# Data Contract — Python ⇄ Godot

This document defines how the Python server and Godot client exchange data.

## Communication Channels

| Channel | Direction | Protocol | Used For |
|---|---|---|---|
| REST API | Client → Server | HTTPS + JSON | Generate script, fetch audio, vote |
| WebSocket | Server → Client | WSS + JSON | Delta updates for live scenes (Feature #27) |

## Authentication

- Every request carries an `X-API-Key` header (see `.env.example` → `API_KEY`).
- WebSocket connections must validate the same key on connect.
- No browser origin/CORS is required — this is a native Godot client.

## Script Payload

Full schema: `shared/schemas/script_schema.json`

```
{
  "version": "1.0",
  "script_id": "uuid",
  "news_ref": { "headline", "source", "published_at", "url" },
  "characters": [{ "id", "name", "voice_id", "mood" }],
  "lines": [
    { "index", "character_id", "text", "emotion", "overlap", "audio_url" }
  ],
  "metadata": { "generated_at", "time_of_day", "mood_drift_applied", "characters_delta" }
}
```

## Emotion Tags

- Registry: `shared/schemas/emotion_tags.json`
- Format: Swahili lowercase snake_case, e.g. `anacheka_kwa_dharau`
- Client maps tag → { voice_style, face parameters, animation intensity }

## Response Envelope

Every endpoint returns:

```
{ "success": bool, "status_code": int, "message": str,
  "error_code": str|null, "request_id": str|null, "data": ... }
```

Error codes: see README "Error Code Taxonomy" (E1001–E5002).

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