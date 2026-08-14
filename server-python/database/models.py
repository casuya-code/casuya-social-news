"""SQLAlchemy ORM models for the Casuya Social News engine."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.engine import Base


class TimeOfDay(str, Enum):
    """Prompt template selection based on local time."""

    asubuhi = "asubuhi"
    mchana = "mchana"
    usiku = "usiku"


class Character(Base):
    """A recurring cast member with memory and mood state."""

    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"char_{uuid4().hex[:8]}"
    )
    name: Mapped[str] = mapped_column(String(128))
    voice_id: Mapped[str] = mapped_column(String(128))
    mood_base: Mapped[str] = mapped_column(String(32), default="utulivu")
    bio: Mapped[str] = mapped_column(Text, default="")
    # Feature #22: current mood drift state (0.0 = neutral).
    mood_drift: Mapped[float] = mapped_column(default=0.0)
    # Feature #25: one-line compressed memory of recent stories.
    memory_summaries: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NewsArticle(Base):
    """A raw scraped article. Deleted after script generation or 48h."""

    __tablename__ = "news_articles"
    __table_args__ = ({"comment": "Raw scraped news; purged per retention policy"},)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    headline: Mapped[str] = mapped_column(String(512))
    source: Mapped[str] = mapped_column(String(128), index=True)
    url: Mapped[str] = mapped_column(String(1024), unique=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    raw_content: Mapped[str] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    script: Mapped["Script | None"] = relationship(back_populates="news_article")


class Script(Base):
    """A generated dramatic script."""

    __tablename__ = "scripts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: uuid4().hex)
    news_article_id: Mapped[int | None] = mapped_column(ForeignKey("news_articles.id"))
    time_of_day: Mapped[TimeOfDay] = mapped_column(SAEnum(TimeOfDay), default=TimeOfDay.mchana)
    full_json: Mapped[dict] = mapped_column(JSON)
    # Retention: full_json compressed to summary after 24h.
    summary: Mapped[str | None] = mapped_column(Text)
    characters_delta: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    news_article: Mapped["NewsArticle | None"] = relationship(back_populates="script")

    # Character-to-script links live in the MemoryEvent table (one-line
    # compressed memories), avoiding a broken many-to-many relationship.


class Vote(Base):
    """A community vote on story direction (Feature #35)."""

    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    script_id: Mapped[str] = mapped_column(ForeignKey("scripts.id"), index=True)
    client_id: Mapped[str] = mapped_column(String(64), index=True)
    direction: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class MemoryEvent(Base):
    """Feature #25: compressed one-line memory entry for a character."""

    __tablename__ = "memory_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id"), index=True)
    script_id: Mapped[str] = mapped_column(ForeignKey("scripts.id"))
    summary: Mapped[str] = mapped_column(Text)
    emotion: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AppMeta(Base):
    """Key/value metadata (schema version, feature flags, app bootstraps)."""

    __tablename__ = "app_meta"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
