"""Async SQLAlchemy engine and session management."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

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


def _ensure_sqlite_dir() -> None:
    """Create parent dir for sqlite file if url points to a local file."""
    url = settings.database_url
    prefix = "sqlite+aiosqlite:///"
    if not url.startswith(prefix):
        return
    db_path = Path(url[len(prefix) :])
    if db_path.is_absolute() or "/" in url[len(prefix) :] or "\\" in url[len(prefix) :]:
        db_path.parent.mkdir(parents=True, exist_ok=True)


async def init_db() -> None:
    """Create tables if they don't exist (dev bootstrap; Alembic will replace this)."""
    _ensure_sqlite_dir()
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
