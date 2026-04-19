"""Shared helpers for Telegram handlers."""

from __future__ import annotations

from aiogram import Bot
from aiogram.types import Message
from loguru import logger

from ...settings import settings
from ..bot_registry import bot_registry


def is_admin(user_id: int) -> bool:
    """True if `user_id` is in `ALLOWED_USER_IDS` (fail-closed if list empty)."""
    allowed = settings.allowed_user_ids_list
    if not allowed:
        return False
    return user_id in allowed


async def deny_if_not_admin(message: Message) -> bool:
    """Reply with denial if `message.from_user` is not an admin. Returns True if denied."""
    if message.from_user is None or not is_admin(message.from_user.id):
        logger.warning(
            f"Admin-only command denied for user_id="
            f"{getattr(message.from_user, 'id', None)}"
        )
        await message.reply("⛔ Admin-only command.")
        return True
    return False


def public_base_url() -> str | None:
    """Derive the public base URL from `settings.webhook_url` (used to build
    per-bot webhook URLs). Returns None if no webhook is configured yet."""
    if not settings.webhook_url:
        return None
    base = settings.webhook_url.removesuffix("/webhook/telegram").rstrip("/")
    return base or None


async def register_webhook_for_token(token: str) -> tuple[bool, str]:
    """Register a Telegram webhook for a managed-bot token.

    Returns (ok, info_string). On failure, `ok=False` and `info_string`
    contains the error message. Uses the shared `BotRegistry`, so the
    `aiogram.Bot` stays cached for subsequent webhook dispatches.
    """
    base = public_base_url()
    if base is None:
        return False, "no public base URL (WEBHOOK_URL not set)"

    target = f"{base}/webhook/telegram/{token}"
    bot: Bot = await bot_registry.get(token)
    try:
        await bot.set_webhook(url=target, drop_pending_updates=True)
    except Exception as exc:
        logger.error(f"register_webhook failed for {target}: {exc}")
        return False, str(exc)

    logger.info(f"🔗 Registered webhook: {target}")
    return True, target
