"""News ingestion pipeline: fetch → dedupe → store → generate script.

The heart of the "endless stories" loop. Pull new articles from the feed,
deduplicate against known URLs, persist best-effort, and run the
contextualizer to produce a dramatic script for each new story.
"""

from __future__ import annotations

from datetime import UTC, datetime

from cache.redis_client import cache
from config.logging_config import get_logger
from database.engine import SessionLocal
from database.models import MemoryEvent, NewsArticle
from nlp.character_state import load_states, set_states
from nlp.contextualizer import contextualize
from nlp.memory import apply_drift, summarize_script
from scraper.dedupe import url_fingerprint
from scraper.news_api_client import NewsApiClient
from scraper.seen_store import load_seen, save_seen

_logger = get_logger("scraper.ingestor")

_SEEN_KEY = "news:seen_urls"


def normalize_article(article: dict) -> dict | None:
    """Map a feed article (News API shape) to the contextualizer input."""
    url = article.get("url", "")
    title = article.get("title") or article.get("headline")
    if not url or not title:
        return None

    source = article.get("source", {})
    if isinstance(source, dict):
        source_name = source.get("name", "unknown")
    else:
        source_name = str(source)

    return {
        "headline": title,
        "source": source_name,
        "url": url,
        "published_at": article.get("publishedAt")
        or article.get("published_at")
        or datetime.now(UTC).isoformat(),
    }


async def _load_seen_fingerprints() -> set[str]:
    """Seed the seen-set from cache (Redis), then the durable file store."""
    seen = load_seen()

    cached = await cache.get(_SEEN_KEY)
    if isinstance(cached, list):
        seen.update(cached)

    try:
        async with SessionLocal() as session:
            rows = await session.execute(
                NewsArticle.__table__.select().with_only_columns(NewsArticle.url)
            )
            for row in rows:
                seen.add(url_fingerprint(row[0]))
    except Exception:  # noqa: BLE001 - DB down, file+cache still work
        _logger.warning("db_unavailable_during_seed")
    return seen


async def _save_seen(seen: set[str]) -> None:
    save_seen(seen)  # durable, survives process restarts
    await cache.set(_SEEN_KEY, list(seen))


async def ingest(fetcher=None, limit: int = 10) -> list[dict]:
    """Fetch and dedupe articles; persist new ones; return them."""
    fetcher = fetcher or NewsApiClient()
    articles = await fetcher.fetch_latest(limit)

    normalized = [n for n in (normalize_article(a) for a in articles) if n]
    seen = await _load_seen_fingerprints()

    fresh = [a for a in normalized if url_fingerprint(a["url"]) not in seen]
    for article in fresh:
        seen.add(url_fingerprint(article["url"]))

    await _save_seen(seen)
    _logger.info("ingest_complete", fetched=len(articles), fresh=len(fresh))

    await _persist_articles(fresh)
    return fresh


async def ingest_and_generate(fetcher=None, limit: int = 10) -> list[dict]:
    """Ingest new articles and generate a script for each. Returns scripts.

    Character memory + mood drift (Features #22/#25) are loaded before
    generation and updated after, so each story builds on the last.
    """
    fresh = await ingest(fetcher, limit)
    states = load_states()

    scripts: list[dict] = []
    for article in fresh:
        script = contextualize(article, states)
        scripts.append(script)
        _update_states(states, summarize_script(script))
        await _persist_memory(script)

    set_states(states)
    _logger.info("generated_scripts", count=len(scripts), active_casts=len(states))
    return scripts


def _update_states(states: dict[str, dict], updates: dict[str, dict]) -> None:
    """Merge per-script memory summaries into the running state."""
    for char_id, update in updates.items():
        previous = states.get(char_id, {"memory": "", "mood": 0.0})
        states[char_id] = {
            "memory": update["memory"],
            "mood": apply_drift(previous.get("mood", 0.0), update["mood"]),
        }


async def _persist_memory(script: dict) -> None:
    """Best-effort DB write of MemoryEvent rows + Character mood_drift."""
    try:
        async with SessionLocal() as session:
            for line in script.get("lines", []):
                char_id = line.get("character_id", "")
                if not char_id:
                    continue
                session.add(
                    MemoryEvent(
                        character_id=char_id,
                        script_id=script["script_id"],
                        summary=script.get("news_ref", {}).get("headline", ""),
                        emotion=line.get("emotion", ""),
                    )
                )
            await session.commit()
    except Exception as exc:  # noqa: BLE001
        _logger.warning("memory_persist_failed", error=str(exc))


async def _persist_articles(articles: list[dict]) -> None:
    """Best-effort persistence; the pipeline must survive DB outages."""
    try:
        async with SessionLocal() as session:
            for article in articles:
                session.add(
                    NewsArticle(
                        headline=article["headline"],
                        source=article["source"],
                        url=article["url"],
                        published_at=datetime.fromisoformat(article["published_at"]),
                        raw_content=article.get("description", ""),
                    )
                )
            await session.commit()
    except Exception as exc:  # noqa: BLE001
        _logger.warning("ingest_persist_failed", error=str(exc))
