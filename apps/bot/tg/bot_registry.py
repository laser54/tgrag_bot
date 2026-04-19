"""Lazy, token-addressed cache of aiogram Bot instances.

One FastAPI backend serves many managed Telegram bots. Each bot needs its own
`aiogram.Bot` session (for `feed_update`, outgoing calls, etc.). We create
those lazily on first use, cache them by token, and close all sessions on
shutdown.
"""

from __future__ import annotations

import asyncio

from aiogram import Bot
from loguru import logger


class BotRegistry:
    """Thread-safe async cache of `aiogram.Bot` instances keyed by token."""

    def __init__(self) -> None:
        self._bots: dict[str, Bot] = {}
        self._lock = asyncio.Lock()

    async def get(self, token: str) -> Bot:
        """Return a cached Bot for `token`, creating it on first access."""
        cached = self._bots.get(token)
        if cached is not None:
            return cached

        async with self._lock:
            cached = self._bots.get(token)
            if cached is not None:
                return cached
            bot = Bot(token=token)
            self._bots[token] = bot
            logger.info(f"🆕 BotRegistry: instantiated bot for token={_mask(token)}")
            return bot

    async def evict(self, token: str) -> None:
        """Drop and close a specific bot session (e.g., on token rotation)."""
        async with self._lock:
            bot = self._bots.pop(token, None)
        if bot is not None:
            try:
                await bot.session.close()
            except Exception as exc:
                logger.warning(f"BotRegistry: failed to close session: {exc}")
            logger.info(f"♻️ BotRegistry: evicted token={_mask(token)}")

    async def shutdown_all(self) -> None:
        """Close every cached bot session. Called from FastAPI lifespan."""
        async with self._lock:
            bots = list(self._bots.items())
            self._bots.clear()
        for token, bot in bots:
            try:
                await bot.session.close()
            except Exception as exc:
                logger.warning(
                    f"BotRegistry: shutdown_all failed for token={_mask(token)}: {exc}"
                )
        if bots:
            logger.info(f"🧹 BotRegistry: closed {len(bots)} cached bot session(s)")


def _mask(token: str) -> str:
    if len(token) >= 12:
        return f"{token[:6]}...{token[-4:]}"
    return "***"


bot_registry = BotRegistry()
