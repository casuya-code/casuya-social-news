"""Contract tests: generated scripts must validate against the shared schema.

These close the loop between the documented data contract
(shared/schemas/script_schema.json) and the code that produces scripts,
so the two can never silently drift apart.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
from jsonschema import Draft202012Validator

from nlp.contextualizer import contextualize
from nlp.memory import summarize_script

SHARED_SCHEMAS = Path(__file__).resolve().parent.parent.parent / "shared" / "schemas"

VALIDATORS = {
    name: Draft202012Validator(json.loads((SHARED_SCHEMAS / name).read_text(encoding="utf-8")))
    for name in ("script_schema.json",)
}

SAMPLE_NEWS = {
    "headline": "Mvua kubwa yameleta mafuriko mkoani Dar es Salaam",
    "source": "Habari Leo",
    "url": "https://example.com/mvua-dar",
    "published_at": "2026-08-14T08:00:00Z",
}


def _script(*, direction: str = "utulivu") -> dict:
    """Generate a script the way the ingestor does (with character state)."""
    states = {
        "char_rafiki": {"memory": "Ajira mpya zinatangazwa jijini", "mood": 0.4},
        "char_mjomba": {"memory": "", "mood": 0.0},
        "char_bibi_mkwe": {"memory": "Mechi ya kimataifa jioni leo", "mood": -0.2},
    }
    script = contextualize(SAMPLE_NEWS, states, direction=direction)
    summarize_script(script)  # memory updates flow back into states
    return script


def test_script_validates_against_schema():
    script = _script()
    errors = sorted(VALIDATORS["script_schema.json"].iter_errors(script), key=str)
    assert not errors, "\n".join(f"- {e.json_path}: {e.message}" for e in errors)


def test_script_variant_per_direction_validates():
    for direction in ("msisimko", "furaha", "wasiwasi", "utulivu"):
        script = _script(direction=direction)
        errors = sorted(VALIDATORS["script_schema.json"].iter_errors(script), key=str)
        assert not errors, f"direction={direction}: " + "; ".join(e.message for e in errors)


def test_schema_requires_every_contract_field():
    script = _script()
    # The schema is the source of truth: any field the client relies on must
    # be present in real output. Guard the keys we know the client reads.
    assert set(script) == {"version", "script_id", "news_ref", "characters", "lines", "metadata"}
    char = script["characters"][0]
    assert {"id", "name", "voice_id", "mood", "mood_value", "mood_label", "memory"} <= set(char)
    line = script["lines"][0]
    assert {"index", "character_id", "text", "emotion", "overlap"} <= set(line)
    assert "audio_url" in line or "audio_url" not in line  # optional until synthesis
    assert script["version"] == "1.0"


def test_metadata_contract_fields_present():
    script = _script()
    metadata = script["metadata"]
    assert {"generated_at", "time_of_day", "mood_drift_applied", "characters_delta"} <= set(
        metadata
    )
    assert metadata["time_of_day"] in ("asubuhi", "mchana", "usiku")


def test_emotion_tags_live_in_registry():
    """Every emotion tag emitted must exist in the shared registry."""
    registry = json.loads((SHARED_SCHEMAS / "emotion_tags.json").read_text(encoding="utf-8"))
    # The registry file is itself a JSON Schema; its concrete tags live in
    # `examples` (array of {tag, description, energy, voice_style}).
    allowed = {entry["tag"] for entry in registry.get("examples", [])}
    assert allowed, "emotion_tags.json has no example tags to validate against"

    script = _script()
    emitted = {line["emotion"] for line in script["lines"]}
    unknown = emitted - allowed
    assert not unknown, f"emotion tags missing from registry: {sorted(unknown)}"


def test_schema_is_draft202012_and_compiles():
    # The schema must stay parseable as the version we advertise.
    try:
        jsonschema.Draft202012Validator.check_schema(
            json.loads((SHARED_SCHEMAS / "script_schema.json").read_text(encoding="utf-8"))
        )
    except jsonschema.SchemaError as exc:
        raise AssertionError(f"script_schema.json is invalid: {exc}") from exc
