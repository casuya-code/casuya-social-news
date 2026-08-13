"""Tests for URL normalization and deduplication."""

from scraper.dedupe import dedupe, normalize_url, url_fingerprint


def test_normalize_url_strips_query_and_case():
    url = "https://Example.com/News/Story?id=42&utm_source=abc#section"
    assert normalize_url(url) == "https://example.com/news/story"


def test_fingerprint_is_stable():
    a = url_fingerprint("https://example.com/a")
    b = url_fingerprint("https://example.com/A")
    assert a == b


def test_dedupe_returns_only_fresh():
    articles = [
        {"url": "https://example.com/1"},
        {"url": "https://example.com/2"},
        {"url": "https://example.com/3"},
    ]
    seen = {url_fingerprint("https://example.com/2")}
    fresh = dedupe(articles, seen)
    assert [a["url"] for a in fresh] == [
        "https://example.com/1",
        "https://example.com/3",
    ]
    # seen set was updated in place
    assert len(seen) == 3


def test_dedupe_skips_empty_urls():
    articles = [{"url": ""}, {"url": "https://example.com/x"}]
    fresh = dedupe(articles, set())
    assert len(fresh) == 1
