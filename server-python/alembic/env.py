"""Alembic migration environment (async, wired to app settings + models).

The database URL comes from `config.settings` (DATABASE_URL / .env), never
from alembic.ini, so migrations and the server always target the same store.
Override with `ALEMBIC_DATABASE_URL` for ad-hoc runs (e.g. SQLite tests):
    $env:ALEMBIC_DATABASE_URL="sqlite+aiosqlite:///./alembic_test.db"
    alembic upgrade head
"""

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from config.settings import get_settings
from database import models  # noqa: F401 - register all tables on Base.metadata
from database.engine import Base

# Alembic Config object (access to values in alembic.ini).
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Models metadata drives autogenerate + compares.
target_metadata = Base.metadata

# Resolve the database URL: explicit config URL → env override → app settings.
configured = config.get_main_option("sqlalchemy.url")
if not configured or configured == "driver://user:pass@localhost/dbname":
    database_url = os.environ.get("ALEMBIC_DATABASE_URL") or get_settings().database_url
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL, no DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and associate a connection with the context."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
