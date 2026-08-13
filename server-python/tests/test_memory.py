"""Tests for character memory and mood drift (Features #22, #25)."""

import pytest

from nlp.contextualizer import contextualize
from nlp.memory import apply_drift, clamp, mood_label, summarize_script

SAMPLE_NEWS = {
    "headline": "Mvua kubwa yameleta mafuriko mkoani Dar es Salaam",
    "source": "Tanzania News",
    "url": "https://example.com/mafuriko-dar",
    "published_at": "2026-08-13T10:00:00Z",
}


def test_summarize_script_returns_per_character_state():
    script = contextualize(SAMPLE_NEWS)
    state = summarize_script(script)
    assert len(state) >= 1
    for _char_id, entry in state.items():
        assert "memory" in entry
        assert entry["memory"] == SAMPLE_NEWS["headline"]
        assert -1.0 <= entry["mood"] <= 1.0


def test_apply_drift_accumulates_and_clamps():
    assert apply_drift(0.0, 0.2) == 0.2
    assert apply_drift(0.9, 0.5) == 1.0  # clamped at upper bound
    assert apply_drift(-0.9, -0.5) == -1.0  # clamped at lower bound


def test_clamp():
    assert clamp(1.5) == 1.0
    assert clamp(-2.0) == -1.0
    assert clamp(0.3) == 0.3


@pytest.mark.parametrize(
    ("mood", "expected"),
    [
        (-0.7, "hana furaha"),
        (-0.3, "ameguswa"),
        (0.0, "hali ya kawaida"),
        (0.3, "ana msisimko"),
        (0.8, "anafuraha"),
    ],
)
def test_mood_label(mood, expected):
    assert mood_label(mood) == expected


def test_contextualize_with_state_sets_drift_flag_and_mood():
    state = {"char_bibi_mkwe": {"memory": "habari za jana", "mood": -0.5}}
    script = contextualize(SAMPLE_NEWS, state)
    assert script["metadata"]["mood_drift_applied"] is True
    for character in script["characters"]:
        assert "mood_value" in character
        assert "mood_label" in character


def test_contextualize_without_state_is_fresh():
    script = contextualize(SAMPLE_NEWS)
    assert script["metadata"]["mood_drift_applied"] is False


def test_same_url_same_state_is_deterministic():
    state = {"char_mjomba": {"memory": "bei ya mafuta", "mood": 0.4}}
    a = contextualize(SAMPLE_NEWS, state)
    b = contextualize(SAMPLE_NEWS, state)
    assert [line["text"] for line in a["lines"]] == [line["text"] for line in b["lines"]]
