"""Tests for the mock feed and ingestion normalization."""

import pytest

from cache.redis_client import MemoryCache
from economy import vote_service
from nlp import character_state
from nlp.contextualizer import _CLOSINGS_BY_DIRECTION
from scraper import seen_store
from scraper.ingestor import ingest, ingest_and_generate, normalize_article
from scraper.mock_feed import MockFeed


@pytest.fixture
def isolated_state(tmp_path, monkeypatch):
    """Isolate durable stores so tests don't pollute each other."""
    monkeypatch.setattr(seen_store, "seen_store_path", lambda: tmp_path / "seen_urls.json")
    monkeypatch.setattr(character_state, "state_path", lambda: tmp_path / "character_state.json")
    monkeypatch.setattr("scraper.ingestor.cache", MemoryCache())
    yield


@pytest.fixture
def isolated_votes(tmp_path, monkeypatch):
    """Point the vote store at a throwaway file."""
    target = tmp_path / "votes.json"
    monkeypatch.setattr("economy.vote_store.votes_path", lambda: target)
    yield target


@pytest.mark.asyncio
async def test_mock_feed_returns_articles():
    feed = MockFeed()
    articles = await feed.fetch_latest(limit=3)
    assert len(articles) == 3
    for article in articles:
        assert "title" in article
        assert "url" in article
        assert "publishedAt" in article


@pytest.mark.asyncio
async def test_ingest_dedupes_between_runs(isolated_state):
    feed = MockFeed()
    first = await ingest(fetcher=feed, limit=10)
    assert len(first) > 0
    second = await ingest(fetcher=feed, limit=10)
    assert len(second) == 0  # all URLs already seen


@pytest.mark.asyncio
async def test_ingest_and_generate_builds_character_memory(isolated_state):
    feed = MockFeed()
    scripts = await ingest_and_generate(fetcher=feed, limit=10)
    assert len(scripts) == 4  # mock feed has 4 unique stories
    # Characters that spoke now have persisted state.
    states = character_state.load_states()
    assert len(states) >= 1
    for entry in states.values():
        assert "memory" in entry
        assert "mood" in entry


@pytest.mark.asyncio
async def test_ingest_steered_by_community_pulse(isolated_state, isolated_votes):
    """Feature #35: the last vote's direction tones the generated closings."""
    vote_service.record_vote("script-pulse", "client-a", "msisimko")
    feed = MockFeed()
    scripts = await ingest_and_generate(fetcher=feed, limit=10)
    assert len(scripts) == 4
    msisimko_closings = _CLOSINGS_BY_DIRECTION["msisimko"]
    for script in scripts:
        assert script["lines"][2]["text"] in msisimko_closings


def test_normalize_article_newsapi_shape():
    article = {
        "title": "Habari kubwa",
        "source": {"name": "Habari Leo"},
        "url": "https://example.com/x",
        "publishedAt": "2026-08-13T06:00:00Z",
    }
    result = normalize_article(article)
    assert result["headline"] == "Habari kubwa"
    assert result["source"] == "Habari Leo"
    assert result["url"] == "https://example.com/x"


def test_normalize_article_handles_string_source():
    article = {
        "title": "Habari",
        "source": "Radio Jambo",
        "url": "https://example.com/y",
    }
    result = normalize_article(article)
    assert result["source"] == "Radio Jambo"


def test_normalize_article_rejects_missing_fields():
    assert normalize_article({"url": "https://example.com/nope"}) is None
    assert normalize_article({"title": "no url"}) is None
