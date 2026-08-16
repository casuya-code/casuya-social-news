"""News ingestion pipeline: fetch → dedupe → store → generate script.

The heart of the "endless stories" loop. Pull new articles from the feed,
deduplicate against known URLs, persist best-effort, and run the
contextualizer to produce a dramatic script for each new story.
"""

from __future__ import annotations

from datetime import UTC, datetime

from api.errors import NewsRateLimitedError, NewsSourceError
from api.websocket_server import broadcast_script
from cache.redis_client import cache
from config.logging_config import get_logger
from config.settings import get_settings
from database.engine import SessionLocal
from database.models import MemoryEvent, NewsArticle
from economy.vote_service import community_pulse
from monitoring.metrics import NEWS_INGESTED, SCRIPTS_GENERATED
from nlp.character_state import load_states, set_states
from nlp.contextualizer import contextualize
from nlp.memory import apply_drift, summarize_script
from scraper.dedupe import url_fingerprint
from scraper.mock_feed import MockFeed
from scraper.news_api_client import NewsApiClient
from scraper.seen_store import load_seen, save_seen
from storage.script_store import save_script
from weather_sync.meteorological_feed import get_weather_feed, mood_offset

_logger = get_logger("scraper.ingestor")
_settings = get_settings()

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
    """Fetch and dedupe articles; persist new ones; return them.

    Falls back to the mock feed if the real source errors (E5001/E5002) so
    the endless-stories loop never stalls on an upstream outage.
    """
    if fetcher is None:
        fetcher = NewsApiClient()

    try:
        articles = await fetcher.fetch_latest(limit)
    except (NewsSourceError, NewsRateLimitedError) as exc:
        _logger.warning("news_fetch_degraded", error_code=exc.error_code, error=str(exc))
        articles = await MockFeed(rotate=_settings.mock_feed_rotate).fetch_latest(limit)

    normalized = [n for n in (normalize_article(a) for a in articles) if n]
    seen = await _load_seen_fingerprints()

    fresh = [a for a in normalized if url_fingerprint(a["url"]) not in seen]
    for article in fresh:
        seen.add(url_fingerprint(article["url"]))

    await _save_seen(seen)
    NEWS_INGESTED.inc(len(fresh))
    _logger.info("ingest_complete", fetched=len(articles), fresh=len(fresh))

    await _persist_articles(fresh)
    return fresh


async def ingest_and_generate(fetcher=None, limit: int = 10) -> list[dict]:
    """Ingest new articles and generate a script for each. Returns scripts.

    Character memory + mood drift (Features #22/#25) are loaded before
    generation and updated after, so each story builds on the last. The
    community's latest vote steers the tone of the batch (Feature #35) and
    current weather biases the cast's moods (Feature #30).
    """
    fresh = await ingest(fetcher, limit)
    states = load_states()
    pulse = community_pulse()
    _logger.info("community_pulse", direction=pulse)

    weather = await get_weather_feed().fetch()
    offset = mood_offset(weather.get("condition", ""))
    if offset:
        _apply_weather_bias(states, offset)
    _logger.info("weather_bias", condition=weather.get("condition"), offset=offset)

    scripts: list[dict] = []
    for article in fresh:
        script = contextualize(article, states, direction=pulse)
        SCRIPTS_GENERATED.labels(direction=pulse).inc()
        script["metadata"]["weather"] = weather
        save_script(script)
        scripts.append(script)
        await broadcast_script(script, states)
        _update_states(states, summarize_script(script))
        await _persist_memory(script)

    set_states(states)
    _logger.info("generated_scripts", count=len(scripts), active_casts=len(states))
    return scripts


def _apply_weather_bias(states: dict[str, dict], offset: float) -> None:
    """Shift every cast member's mood by the weather offset (Feature #30)."""
    for state in states.values():
        state["mood"] = round(apply_drift(state.get("mood", 0.0), offset), 3)


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
