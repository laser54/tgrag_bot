"""User-facing handlers: /start, /menu, catch-all text.

Registered AFTER `admin_router`, so admin-filtered /start wins for admins.
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    Message,
    WebAppInfo,
)
from loguru import logger

from ...settings import settings

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    logger.info(f"/start from {message.from_user.id if message.from_user else '?'}")
    await message.reply(
        "🤖 Hello! I'm Telegram RAG Bot\n\n"
        "I can analyze documents and answer questions. "
        "Upload files and ask questions!\n\n"
        "Use /menu to access bot features."
    )

    try:
        await message.bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=MenuButtonWebApp(
                text="Document Hub",
                web_app=WebAppInfo(url=settings.webapp_url_full),
            ),
        )
    except Exception as exc:
        logger.debug(f"Failed to configure chat menu button: {exc}")


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    logger.info(f"/menu from {user_id}")

    if (
        settings.allowed_user_ids
        and user_id is not None
        and user_id not in settings.allowed_user_ids_list
    ):
        logger.warning(f"Access denied for user {user_id}")
        await message.reply("❌ You don't have access to this bot.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📱 Open Application",
                    web_app=WebAppInfo(url=settings.webapp_url_full),
                )
            ]
        ]
    )

    await message.reply(
        "🎛️ Bot Menu\n\n"
        "Click the button below to open the interface for working with documents:",
        reply_markup=keyboard,
    )

    try:
        await message.bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=MenuButtonWebApp(
                text="Document Hub",
                web_app=WebAppInfo(url=settings.webapp_url_full),
            ),
        )
    except Exception as exc:
        logger.debug(f"Failed to configure chat menu button: {exc}")


@router.message()
async def handle_text(message: Message) -> None:
    txt = message.text or ""
    logger.debug(
        f"Text from {message.from_user.id if message.from_user else '?'}: "
        f"'{txt[:80]}'"
    )
    await message.reply(
        "📝 Message received!\n\n"
        "For now I only accept messages. "
        "Soon there will be RAG logic for document analysis!"
    )
