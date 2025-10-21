"""Telegram bot handlers for webhook mode."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    Message,
    WebAppInfo,
)

from ..settings import settings

# Create router
router = Router()

logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    logger.info(f"/start from {message.from_user.id}")

    welcome_text = (
        "🤖 Hello! I'm Telegram RAG Bot\n\n"
        "I can analyze documents and answer questions. "
        "Upload files and ask questions!\n\n"
        "Use /menu to access bot features."
    )

    await message.reply(welcome_text)
    logger.debug(f"Welcome sent to {message.from_user.id}")

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
    """Handle /menu command with WebApp button."""
    logger.info(f"/menu from {message.from_user.id}")

    # Check if user is allowed (if restrictions are set)
    if (
        settings.allowed_user_ids
        and message.from_user.id not in settings.allowed_user_ids_list
    ):
        logger.warning(f"Access denied for user {message.from_user.id}")
        await message.reply("❌ You don't have access to this bot.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📱 Open Application",
                    web_app={"url": settings.webapp_url_full},
                )
            ]
        ]
    )

    menu_text = (
        "🎛️ Bot Menu\n\n"
        "Click the button below to open the interface for working with documents:"
    )

    await message.reply(menu_text, reply_markup=keyboard)
    logger.debug(f"Menu sent to {message.from_user.id}")

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
    """Handle regular text messages."""
    logger.debug(
        f"Text from {message.from_user.id}: '{message.text[:80] if message.text else ''}'"
    )

    # For now, just acknowledge the message
    # Later this will be replaced with RAG logic
    await message.reply(
        "📝 Message received!\n\n"
        "For now I only accept messages. "
        "Soon there will be RAG logic for document analysis!"
    )
    logger.debug(f"Ack sent to {message.from_user.id}")
