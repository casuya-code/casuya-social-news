"""SQLAlchemy engine and async session factory."""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from api.errors import MigrationRequiredError
from config.logging_config import get_logger
from config.settings import get_settings

_logger = get_logger("database.engine")
_settings = get_settings()

# Bump when the ORM models change shape (schema migrations must follow).
SCHEMA_VERSION = 1

engine = create_async_engine(
    _settings.database_url,
    pool_size=_settings.database_pool_size,
    max_overflow=_settings.database_max_overflow,
    echo=_settings.app_debug,
)

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a database session."""
    async with SessionLocal() as session:
        yield session


async def check_schema_version() -> None:
    """Verify the database schema matches the codebase; raise E3003 otherwise.

    Best-effort: unreachable databases are not treated as a schema mismatch,
    so graceful degradation still applies when Postgres is absent.
    """
    try:
        async with SessionLocal() as session:
            row = await session.execute(
                text("SELECT value FROM app_meta WHERE key = 'schema_version'")
            )
            stored = int(row.scalar())
    except Exception as exc:  # noqa: BLE001
        _logger.debug("schema_check_unavailable", error=str(exc))
        return
    if stored != SCHEMA_VERSION:
        raise MigrationRequiredError(
            "Database schema version "
            f"{stored} != expected {SCHEMA_VERSION}; run alembic upgrade head"
        )
