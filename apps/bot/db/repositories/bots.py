"""Repository for the `bots` table."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Bot, BotType


class BotsRepository:
    """Async data access for managed Telegram bots."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def list_all(self) -> list[Bot]:
        result = await self._s.execute(select(Bot).order_by(Bot.id))
        return list(result.scalars().all())

    async def get_by_id(self, bot_id: int) -> Bot | None:
        return await self._s.get(Bot, bot_id)

    async def get_by_token(self, token: str) -> Bot | None:
        result = await self._s.execute(select(Bot).where(Bot.token == token))
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        token: str,
        owner_id: int,
        name: str,
        bot_type: BotType = BotType.rag,
    ) -> Bot:
        bot = Bot(token=token, owner_id=owner_id, name=name, bot_type=bot_type)
        self._s.add(bot)
        await self._s.commit()
        await self._s.refresh(bot)
        return bot

    async def set_bot_type(self, bot_id: int, bot_type: BotType) -> Bot | None:
        bot = await self._s.get(Bot, bot_id)
        if bot is None:
            return None
        bot.bot_type = bot_type
        await self._s.commit()
        await self._s.refresh(bot)
        return bot
