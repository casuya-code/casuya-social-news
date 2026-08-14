"""Tests for the contextualizer (news → script) and emotion tagger."""

import pytest

from nlp.contextualizer import contextualize
from nlp.emotion_tagger import tag_line

SAMPLE_NEWS = {
    "headline": "Mvua kubwa yameleta mafuriko mkoani Dar es Salaam",
    "source": "Tanzania News",
    "url": "https://example.com/mafuriko-dar",
    "published_at": "2026-08-13T10:00:00Z",
}


def test_contextualize_returns_valid_script():
    script = contextualize(SAMPLE_NEWS)
    assert script["version"] == "1.0"
    assert script["script_id"]
    assert script["news_ref"]["headline"] == SAMPLE_NEWS["headline"]
    assert len(script["characters"]) >= 1
    assert len(script["lines"]) >= 1


def test_lines_have_required_fields():
    script = contextualize(SAMPLE_NEWS)
    for line in script["lines"]:
        assert "index" in line
        assert "character_id" in line
        assert "text" in line
        assert "emotion" in line


def test_same_url_produces_same_script():
    a = contextualize(SAMPLE_NEWS)
    b = contextualize(SAMPLE_NEWS)
    # script_id is random (uuid) but structure/text must match
    assert [line["text"] for line in a["lines"]] == [line["text"] for line in b["lines"]]


@pytest.mark.parametrize("index", [0, 1, 2, 5, 10])
def test_tag_line_returns_registry_style(index):
    tag = tag_line(index)
    assert isinstance(tag, str)
    assert len(tag) > 3


def test_direction_changes_closing_but_keeps_structure():
    """Feature #35: direction tunes the scene resolution, not the shape."""
    excited = contextualize(SAMPLE_NEWS, direction="msisimko")
    calm = contextualize(SAMPLE_NEWS, direction="utulivu")
    assert len(excited["lines"]) == len(calm["lines"])
    assert excited["lines"][2]["text"] != calm["lines"][2]["text"]


def test_direction_is_deterministic():
    a = contextualize(SAMPLE_NEWS, direction="wasiwasi")
    b = contextualize(SAMPLE_NEWS, direction="wasiwasi")
    assert [line["text"] for line in a["lines"]] == [line["text"] for line in b["lines"]]


def test_direction_defaults_to_calm():
    default = contextualize(SAMPLE_NEWS)
    calm = contextualize(SAMPLE_NEWS, direction="utulivu")
    assert [line["text"] for line in default["lines"]] == [line["text"] for line in calm["lines"]]


def test_slang_opening_possible():
    """Feature #26: some scripts open with urban slang."""
    from nlp import contextualizer as ctx

    saw_slang = False
    for seed_url in (f"https://example.com/slang-{i}" for i in range(40)):
        news = {**SAMPLE_NEWS, "url": seed_url}
        script = ctx.build_mock_script(news)
        saw_slang = any(
            line["index"] == 0 and any(line["text"].startswith(s) for s in ctx._SLANG_OPENINGS)
            for line in script["lines"]
        )
        if saw_slang:
            break
    assert saw_slang, "no slang opening found across 40 seeds"


def test_methali_possible_in_closing():
    """Feature #1: closings sometimes resolve with a Swahili proverb."""
    from nlp import contextualizer as ctx

    saw_proverb = False
    for seed_url in (f"https://example.com/methali-{i}" for i in range(60)):
        news = {**SAMPLE_NEWS, "url": seed_url}
        script = ctx.build_mock_script(news)
        closing = script["lines"][2]["text"]
        if any(p in closing for p in ctx._PROVERBS):
            saw_proverb = True
            break
    assert saw_proverb, "no methali closing found across 60 seeds"


def test_overlap_cues_with_heated_state():
    """Feature #6: heated characters produce overlapping lines."""
    from nlp import contextualizer as ctx

    hot_states = {
        "char_rafiki": {"memory": "", "mood": 0.7},
        "char_bibi_mkwe": {"memory": "", "mood": 0.6},
    }
    saw_overlap = False
    for seed_url in (f"https://example.com/heat-{i}" for i in range(30)):
        news = {**SAMPLE_NEWS, "url": seed_url}
        script = ctx.build_mock_script(news, hot_states)
        if any(line["overlap"] for line in script["lines"]):
            saw_overlap = True
            break
    assert saw_overlap, "no overlap cue found across 30 hot seeds"


def test_emotion_carryover_in_closing():
    """Feature #5: a character's mood carries into their closing emotion."""
    from nlp import contextualizer as ctx

    sad_states = {
        "char_rafiki": {"memory": "", "mood": -0.8},
        "char_bibi_mkwe": {"memory": "", "mood": 0.0},
    }
    saw_carried = False
    for seed_url in (f"https://example.com/carry-{i}" for i in range(30)):
        news = {**SAMPLE_NEWS, "url": seed_url}
        script = ctx.build_mock_script(news, sad_states)
        closing = script["lines"][2]
        if closing["emotion"] in ("anakasirika", "anahofia", "anasikitika"):
            saw_carried = True
            break
    assert saw_carried, "no negative carryover emotion found across 30 seeds"


def test_determinism_holds_with_enrichment():
    """New layers must not break seeded determinism."""
    states = {"char_rafiki": {"memory": "Habari ya zamani", "mood": 0.5}}
    a = contextualize(SAMPLE_NEWS, states, direction="msisimko")
    b = contextualize(SAMPLE_NEWS, states, direction="msisimko")
    assert [line["text"] for line in a["lines"]] == [line["text"] for line in b["lines"]]
    assert [line["emotion"] for line in a["lines"]] == [line["emotion"] for line in b["lines"]]
    assert [line["overlap"] for line in a["lines"]] == [line["overlap"] for line in b["lines"]]
