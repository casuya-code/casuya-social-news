"""URL-based deduplication for fetched news articles.

News feeds return overlapping content across fetches. Dedup prevents the
engine from generating a script for the same story twice.
"""

from __future__ import annotations

from hashlib import sha1
from urllib.parse import urlparse


def normalize_url(url: str) -> str:
    """Stable dedup key: lowercase scheme+host+path, strip query/fragment."""
    try:
        parsed = urlparse(url.strip())
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    except ValueError:
        normalized = url.strip()
    return normalized.lower()


def url_fingerprint(url: str) -> str:
    """Return a stable sha1 fingerprint for a URL."""
    return sha1(normalize_url(url).encode("utf-8")).hexdigest()


def dedupe(articles: list[dict], seen: set[str]) -> list[dict]:
    """Return articles whose URL fingerprints are not already in `seen`."""
    fresh: list[dict] = []
    for article in articles:
        url = article.get("url", "")
        if not url:
            continue
        fingerprint = url_fingerprint(url)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        fresh.append(article)
    return fresh
