"""News endpoints: list latest ingested stories, trigger an ingestion."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from config.logging_config import get_logger
from database.engine import SessionLocal
from database.models import NewsArticle
from scraper.ingestor import ingest_and_generate
from security.api_key_auth import verify_api_key

_logger = get_logger("api.news")

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("/latest")
async def latest_news(limit: int = 20) -> dict:
    """Return the most recent ingested articles."""
    articles: list[dict] = []
    try:
        async with SessionLocal() as session:
            result = await session.execute(
                NewsArticle.__table__.select()
                .order_by(NewsArticle.__table__.c.published_at.desc())
                .limit(limit)
            )
            articles = [
                {
                    "id": row.id,
                    "headline": row.headline,
                    "source": row.source,
                    "url": row.url,
                    "published_at": row.published_at.isoformat() if row.published_at else None,
                }
                for row in result
            ]
    except Exception as exc:  # noqa: BLE001 - DB down
        _logger.warning("latest_news_db_down", error=str(exc))
        articles = []

    return {"articles": articles, "count": len(articles)}


@router.post("/refresh")
async def refresh_news(limit: int = 10) -> dict:
    """Pull new articles now and generate a script for each fresh story."""
    scripts = await ingest_and_generate(limit=limit)
    return {"ingested": len(scripts), "scripts": scripts}
