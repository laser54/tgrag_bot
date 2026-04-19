"""Admin endpoints for managed Telegram bots."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from ..db import get_session
from ..db.models import BotType
from ..db.repositories import BotsRepository

router = APIRouter(prefix="/api/bots", tags=["bots"])


class BotOut(BaseModel):
    """Public representation of a managed bot (token is masked)."""

    id: int
    name: str
    bot_type: BotType
    owner_id: int
    token_preview: str
    created_at: datetime

    @classmethod
    def from_orm_bot(cls, bot) -> BotOut:
        token = bot.token or ""
        preview = f"{token[:6]}...{token[-4:]}" if len(token) >= 12 else "***"
        return cls(
            id=bot.id,
            name=bot.name,
            bot_type=bot.bot_type,
            owner_id=bot.owner_id,
            token_preview=preview,
            created_at=bot.created_at,
        )


class BotCreateIn(BaseModel):
    """Payload to register a managed bot (dev/admin seed)."""

    token: str = Field(..., min_length=10, max_length=256)
    owner_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=128)
    bot_type: BotType = BotType.rag


@router.get("", response_model=list[BotOut])
async def list_bots() -> list[BotOut]:
    async with get_session() as session:
        repo = BotsRepository(session)
        bots = await repo.list_all()
        return [BotOut.from_orm_bot(b) for b in bots]


@router.post("", response_model=BotOut, status_code=status.HTTP_201_CREATED)
async def create_bot(payload: BotCreateIn) -> BotOut:
    async with get_session() as session:
        repo = BotsRepository(session)
        try:
            bot = await repo.create(
                token=payload.token,
                owner_id=payload.owner_id,
                name=payload.name,
                bot_type=payload.bot_type,
            )
        except IntegrityError as exc:
            logger.warning(f"Bot create conflict: {exc.orig}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bot with this token already exists",
            ) from exc
        logger.info(
            f"➕ Registered bot id={bot.id} name={bot.name!r} type={bot.bot_type}"
        )
        return BotOut.from_orm_bot(bot)
