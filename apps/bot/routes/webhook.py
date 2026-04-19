"""Dynamic webhook endpoint: routes Telegram updates by bot token.

Path: `POST /webhook/telegram/{bot_token}`

Flow:
1. Resolve the managed bot by token from SQLite (404 on unknown).
2. Obtain its `aiogram.Bot` instance from the `BotRegistry` (lazy init).
3. Feed the Update into the shared Dispatcher.

The single-bot legacy endpoint `POST /webhook/telegram` in `main.py`
remains in place as a transitional fallback.
"""

from __future__ import annotations

from aiogram.types import Update
from fastapi import APIRouter, HTTPException, Path, Request, status
from loguru import logger

from ..db import get_session
from ..db.repositories import BotsRepository
from ..tg.bot_registry import bot_registry

router = APIRouter(tags=["webhook"])


@router.post("/webhook/telegram/{bot_token}")
async def dynamic_telegram_webhook(
    request: Request,
    bot_token: str = Path(..., min_length=10, max_length=256),
) -> dict[str, str]:
    """Receive and dispatch a Telegram update for a specific managed bot."""
    async with get_session() as session:
        repo = BotsRepository(session)
        bot_row = await repo.get_by_token(bot_token)

    if bot_row is None:
        logger.warning(f"Webhook: unknown token prefix={bot_token[:6]}... rejected")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unknown bot token"
        )

    dp = getattr(request.app.state, "dp", None)
    if dp is None:
        logger.error("Webhook: dispatcher not initialized (demo mode?)")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dispatcher not initialized",
        )

    try:
        update_data = await request.json()
    except Exception as exc:
        logger.warning(f"Webhook: malformed JSON for bot_id={bot_row.id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON"
        ) from exc

    update_id = update_data.get("update_id", "unknown")
    logger.debug(
        f"Webhook: bot_id={bot_row.id} type={bot_row.bot_type} update_id={update_id}"
    )

    bot = await bot_registry.get(bot_token)
    try:
        update = Update(**update_data)
        await dp.feed_update(bot=bot, update=update)
    except Exception as exc:
        logger.error(
            f"Webhook: dispatch failed for bot_id={bot_row.id} update_id={update_id}: {exc}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dispatch failed",
        ) from exc

    return {"status": "ok"}
