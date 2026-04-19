"""Admin-only commands for managing the bot swarm.

Uses Telegram Bot API 9.6 managed-bot flow:
  1. Admin opens the manager bot and presses the reply-keyboard button with
     `KeyboardButtonRequestManagedBot`. Telegram UI walks them through
     creating a new bot that will be owned/managed by the manager bot.
  2. Upon completion, the manager bot receives a service `Message` with a
     populated `managed_bot_created` field (see Update.message).
  3. We call `bot.get_managed_bot_token(user_id=<new_bot_id>)` to fetch the
     token, persist the bot in SQLite, and register its webhook under
     `/webhook/telegram/{token}`.

Requires the manager bot to be configured in @BotFather's "Manage Bots" Mini
App (enables KeyboardButtonRequestManagedBot for it).
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, Filter
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRequestManagedBot,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from loguru import logger
from sqlalchemy.exc import IntegrityError

from ...db import get_session
from ...db.models import BotType
from ...db.repositories import BotsRepository
from .common import deny_if_not_admin, is_admin, register_webhook_for_token

router = Router()

# Constant request_id for the managed-bot keyboard button. Must be unique
# within a single message; a single button per message is fine with `1`.
_REQUEST_MANAGED_BOT_ID = 1


class AdminFilter(Filter):
    """Match only messages from admin users (ALLOWED_USER_IDS)."""

    async def __call__(self, event) -> bool:  # type: ignore[override]
        user = getattr(event, "from_user", None)
        return user is not None and is_admin(user.id)


def _create_managed_bot_keyboard() -> ReplyKeyboardMarkup:
    """Reply keyboard offering the native 'create managed bot' UI."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="➕ Create managed bot",
                    request_managed_bot=KeyboardButtonRequestManagedBot(
                        request_id=_REQUEST_MANAGED_BOT_ID,
                    ),
                )
            ],
            [KeyboardButton(text="📋 /listbots")],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Admin panel",
    )


def _bot_type_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔎 RAG", callback_data=f"set_type:{bot_id}:rag"
                ),
                InlineKeyboardButton(
                    text="🧪 Researcher",
                    callback_data=f"set_type:{bot_id}:researcher",
                ),
                InlineKeyboardButton(
                    text="🎓 Mentor", callback_data=f"set_type:{bot_id}:mentor"
                ),
            ],
        ]
    )


@router.message(Command("start"), AdminFilter())
async def cmd_start_admin(message: Message) -> None:
    """Admin-flavored /start: exposes the managed-bot creation keyboard."""
    await message.reply(
        "👑 <b>Admin panel</b>\n\n"
        "Tap <b>Create managed bot</b> below to spawn a new bot under this "
        "swarm. Telegram will walk you through naming/username and then "
        "send the new bot's info back here automatically.\n\n"
        "Other commands:\n"
        "• /listbots — list managed bots\n"
        "• /cancel — cancel any pending action\n\n"
        "ℹ️ Requires this manager bot to be enabled in @BotFather → "
        "Manage Bots Mini App.",
        parse_mode="HTML",
        reply_markup=_create_managed_bot_keyboard(),
    )


@router.message(Command("listbots"), AdminFilter())
async def cmd_listbots(message: Message) -> None:
    async with get_session() as session:
        bots = await BotsRepository(session).list_all()

    if not bots:
        await message.reply("No managed bots yet. Use the keyboard button to add one.")
        return

    lines = ["🗂 <b>Managed bots</b>:"]
    for b in bots:
        token_preview = (
            f"{b.token[:6]}...{b.token[-4:]}" if len(b.token) >= 12 else "***"
        )
        lines.append(
            f"• #{b.id} <b>{b.name}</b> — type=<code>{b.bot_type.value}</code>, "
            f"owner={b.owner_id}, token=<code>{token_preview}</code>"
        )
    await message.reply("\n".join(lines), parse_mode="HTML")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message) -> None:
    if await deny_if_not_admin(message):
        return
    await message.reply("✅ OK.", reply_markup=ReplyKeyboardRemove())


@router.message(F.managed_bot_created)
async def on_managed_bot_created(message: Message) -> None:
    """Service message: user finished creating a managed bot via our keyboard."""
    if message.from_user is None or not is_admin(message.from_user.id):
        logger.warning(
            "managed_bot_created from non-admin user_id="
            f"{getattr(message.from_user, 'id', None)} — ignored"
        )
        return

    mbc = message.managed_bot_created
    # aiogram renames the `bot` field to `bot_user` to avoid clashing with the
    # reserved `bot` context attribute on TelegramObject.
    new_bot = getattr(mbc, "bot_user", None) if mbc is not None else None
    if new_bot is None:
        await message.reply("⚠️ Empty managed_bot_created payload, ignoring.")
        return
    owner_id = message.from_user.id
    name = new_bot.first_name or (
        f"@{new_bot.username}" if new_bot.username else f"bot#{new_bot.id}"
    )

    logger.info(
        f"Phase2: managed_bot_created user_id={new_bot.id} "
        f"@{new_bot.username} owner={owner_id}"
    )

    try:
        token: str = await message.bot.get_managed_bot_token(user_id=new_bot.id)
    except Exception as exc:
        logger.error(f"get_managed_bot_token failed for {new_bot.id}: {exc}")
        await message.reply(
            "❌ Could not fetch token from Telegram: " f"<code>{exc}</code>",
            parse_mode="HTML",
        )
        return

    async with get_session() as session:
        repo = BotsRepository(session)
        try:
            bot_row = await repo.create(
                token=token,
                owner_id=owner_id,
                name=name,
                bot_type=BotType.rag,
            )
        except IntegrityError:
            existing = await repo.get_by_token(token)
            if existing is None:
                await message.reply("⚠️ Token already registered but row missing.")
                return
            bot_row = existing
            logger.info(f"Phase2: token already registered → bot_id={bot_row.id}")

    ok, info = await register_webhook_for_token(token)
    webhook_line = (
        f"🔗 Webhook: <code>{info}</code>" if ok else f"⚠️ Webhook not set ({info})"
    )
    logger.info(
        f"Phase2: persisted bot_id={bot_row.id} owner={owner_id} " f"webhook_ok={ok}"
    )

    await message.reply(
        "✅ <b>Managed bot registered</b>\n\n"
        f"• id: <code>{bot_row.id}</code>\n"
        f"• name: <b>{name}</b>\n"
        f"• username: @{new_bot.username or '?'}\n"
        f"• default type: <code>{bot_row.bot_type.value}</code>\n"
        f"{webhook_line}\n\n"
        "Change the bot type:",
        parse_mode="HTML",
        reply_markup=_bot_type_keyboard(bot_row.id),
    )


@router.callback_query(F.data.startswith("set_type:"))
async def cb_set_type(cq: CallbackQuery) -> None:
    if cq.from_user is None or not is_admin(cq.from_user.id):
        await cq.answer("Admin only", show_alert=True)
        return

    try:
        _, bot_id_s, type_s = (cq.data or "").split(":", 2)
        bot_id = int(bot_id_s)
        new_type = BotType(type_s)
    except (ValueError, AttributeError):
        await cq.answer("Bad payload", show_alert=True)
        return

    async with get_session() as session:
        updated = await BotsRepository(session).set_bot_type(bot_id, new_type)

    if updated is None:
        await cq.answer("Bot not found", show_alert=True)
        return

    if cq.message is not None:
        try:
            await cq.message.edit_reply_markup(reply_markup=_bot_type_keyboard(bot_id))
        except Exception:
            pass
    await cq.answer(f"Type set to {new_type.value}")
    logger.info(f"Phase2: bot_id={bot_id} type→{new_type.value}")
