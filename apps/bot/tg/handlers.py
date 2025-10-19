"""Telegram bot handlers for webhook mode."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..settings import settings

# Create router
router = Router()

logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    welcome_text = (
        "🤖 Привет! Я Telegram RAG Bot\n\n"
        "Я могу анализировать документы и отвечать на вопросы. "
        "Загружайте файлы и задавайте вопросы!\n\n"
        "Используйте /menu для доступа к функциям бота."
    )

    await message.reply(welcome_text)


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    """Handle /menu command with WebApp button."""
    # Check if user is allowed (if restrictions are set)
    if (
        settings.allowed_user_ids
        and message.from_user.id not in settings.allowed_user_ids_list
    ):
        await message.reply("❌ У вас нет доступа к этому боту.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📱 Открыть приложение", web_app={"url": settings.webapp_url}
                )
            ]
        ]
    )

    menu_text = (
        "🎛️ Меню бота\n\n"
        "Нажмите кнопку ниже, чтобы открыть интерфейс для работы с документами:"
    )

    await message.reply(menu_text, reply_markup=keyboard)


@router.message()
async def handle_text(message: Message) -> None:
    """Handle regular text messages."""
    # For now, just acknowledge the message
    # Later this will be replaced with RAG logic
    await message.reply(
        "📝 Сообщение получено!\n\n"
        "Пока что я только принимаю сообщения. "
        "Скоро здесь будет RAG-логика для анализа документов!"
    )
