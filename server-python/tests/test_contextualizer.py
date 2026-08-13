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
