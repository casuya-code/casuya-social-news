"""Mock Swahili news feed — deterministic source for development and tests.

Mirrors the News API article shape so the ingestor works identically with
either source. No API key required. Used when NEWS_API_KEY is not set.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from config.settings import get_settings

_MOCK_ARTICLES = [
    {
        "title": "Mvua kubwa yameleta mafuriko mkoani Dar es Salaam",
        "source": {"name": "Habari Leo"},
        "url": "https://example.com/mafuriko-dar",
        "publishedAt": "2026-08-13T06:00:00Z",
        "description": "Wakazi wa mkoa wa Dar es Salaam wameathirika na mafuriko.",
    },
    {
        "title": "Bei ya mafuta ya kupanda wiki hii",
        "source": {"name": "Tanzania Times"},
        "url": "https://example.com/bei-mafuta",
        "publishedAt": "2026-08-13T05:30:00Z",
        "description": "Wataalamu wanatarajia kupanda kwa bei ya mafuta.",
    },
    {
        "title": "Timu ya Taifa yaandaa mechi ya kimataifa jioni leo",
        "source": {"name": "Michezo Bora"},
        "url": "https://example.com/timu-taifa",
        "publishedAt": "2026-08-13T04:45:00Z",
        "description": "Mechi itafanyika uwanja wa taifa kuanzia saa tatu usiku.",
    },
    {
        "title": "Kampuni ya teknolojia yatangaza ajira mpya 500",
        "source": {"name": "Habari Leo"},
        "url": "https://example.com/ajira-mpya",
        "publishedAt": "2026-08-13T04:00:00Z",
        "description": "Fursa mpya za ajira kwa vijana wenye ujuzi wa kidijitali.",
    },
]


class MockFeed:
    """Serves a rotating list of mock articles, refreshed by timestamp.

    With `rotate=True`, each fetch round produces NEW URLs so the endless
    loop keeps generating stories — useful for demos and for watching
    character memory/mood build over time. The round counter persists to
    disk so restarts continue where they left off.
    """

    def __init__(self, articles: list[dict] | None = None, rotate: bool = False) -> None:
        self._articles = articles or _MOCK_ARTICLES
        self._rotate = rotate
        self._round = self._load_round() if rotate else 0

    @staticmethod
    def _round_file():
        return get_settings().storage_dir / "mock_round.txt"

    def _load_round(self) -> int:
        path = self._round_file()
        try:
            if path.exists():
                return int(path.read_text(encoding="utf-8").strip())
        except Exception:  # noqa: BLE001 - corrupt/missing → start at 0
            pass
        return 0

    def _bump_round(self) -> int:
        self._round += 1
        path = self._round_file()
        try:
            path.write_text(str(self._round), encoding="utf-8")
        except Exception:  # noqa: BLE001 - persistence must not break the loop
            pass
        return self._round

    async def fetch_latest(self, limit: int = 10) -> list[dict]:
        """Return articles with fresh timestamps (so dedup has variety)."""
        if self._rotate:
            self._bump_round()
        now = datetime.now(UTC)
        out = []
        for i, article in enumerate(self._articles[:limit]):
            item = dict(article)
            item["publishedAt"] = (now - timedelta(minutes=30 * i)).isoformat()
            if self._rotate and self._round > 1:
                # Distinct path per round → new fingerprint → not deduped.
                item["url"] = f"{article['url']}/{self._round}"
            out.append(item)
        return out
