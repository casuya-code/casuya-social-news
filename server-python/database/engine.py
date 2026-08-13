"""SQLAlchemy engine and async session factory."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config.settings import get_settings

_settings = get_settings()

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
