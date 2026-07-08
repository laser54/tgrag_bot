"""Async SQLAlchemy engine and session management."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig
from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..settings import settings
from . import models  # noqa: F401  # ensure models are registered on Base.metadata
from .base import Base

_engine = create_async_engine(settings.database_url, future=True)
_SessionFactory = async_sessionmaker(
    _engine, expire_on_commit=False, class_=AsyncSession
)

_ALEMBIC_INI = Path(__file__).resolve().parents[3] / "alembic.ini"


def _ensure_sqlite_dir() -> None:
    """Create parent dir for sqlite file if url points to a local file."""
    url = settings.database_url
    prefix = "sqlite+aiosqlite:///"
    if not url.startswith(prefix):
        return
    db_path = Path(url[len(prefix) :])
    if db_path.is_absolute() or "/" in url[len(prefix) :] or "\\" in url[len(prefix) :]:
        db_path.parent.mkdir(parents=True, exist_ok=True)


def _run_alembic_upgrade() -> None:
    """Run `alembic upgrade head` synchronously (env.py owns the async loop).

    Executed in a worker thread so its internal ``asyncio.run`` does not
    collide with the running event loop.
    """
    cfg = AlembicConfig(str(_ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(cfg, "head")


async def init_db() -> None:
    """Bring the schema to the latest migration revision.

    Set ``DEV_CREATE_ALL=true`` to fall back to ``Base.metadata.create_all``
    (emergency only); migrations remain the source of truth.
    """
    _ensure_sqlite_dir()
    if settings.dev_create_all:
        logger.warning("DEV_CREATE_ALL=true — creating tables via create_all")
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    else:
        await asyncio.to_thread(_run_alembic_upgrade)
    logger.info(f"🗄️ DB ready at {settings.database_url}")


async def shutdown_db() -> None:
    """Dispose of the engine."""
    await _engine.dispose()


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield an async session with automatic rollback on exception."""
    async with _SessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
