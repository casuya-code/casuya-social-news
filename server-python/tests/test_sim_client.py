"""Tests for the simulated-client demo tooling."""

from tools.sim_client import DIRECTIONS, _print_story, _vote_payload


def test_vote_payload_has_valid_direction():
    payload = _vote_payload("a" * 32, "client-1")
    assert payload["script_id"] == "a" * 32
    assert payload["client_id"] == "client-1"
    assert payload["direction"] in DIRECTIONS


def test_print_story_renders_headline_and_deltas():
    message = {
        "type": "script_delta",
        "script_id": "a" * 32,
        "headline": "Mvua kubwa",
        "time_of_day": "mchana",
        "characters_delta": [
            {
                "id": "char_bibi",
                "name": "Bibi Mkwe",
                "mood": "uchangamfu",
                "mood_label": "anafuraha",
                "memory": "Alipata habari",
            },
        ],
    }
    rendered = _print_story(message)
    assert "[STORY] Mvua kubwa" in rendered
    assert "time: mchana" in rendered
    assert "Bibi Mkwe" in rendered
    assert "anafuraha" in rendered
    assert "Alipata habari" in rendered


def test_print_story_falls_back_to_character_id():
    message = {
        "type": "script_delta",
        "headline": "Habari",
        "characters_delta": [{"id": "char_mjomba", "mood": "hasira"}],
    }
    rendered = _print_story(message)
    assert "char_mjomba" in rendered
    assert "hasira" in rendered
    assert "memory=—" in rendered
