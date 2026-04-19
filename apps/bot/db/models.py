"""ORM models for the bot swarm."""

from __future__ import annotations

import enum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class BotType(str, enum.Enum):
    """Execution graph a bot should be routed to."""

    rag = "rag"
    researcher = "researcher"
    mentor = "mentor"


class DocumentStatus(str, enum.Enum):
    """Lifecycle state of an ingested document."""

    queued = "queued"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class Bot(Base, TimestampMixin):
    """A Telegram bot managed by the swarm."""

    __tablename__ = "bots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    bot_type: Mapped[BotType] = mapped_column(
        SAEnum(BotType, name="bot_type", native_enum=False, length=32),
        nullable=False,
        default=BotType.rag,
    )

    documents: Mapped[list[Document]] = relationship(
        back_populates="bot", cascade="all, delete-orphan"
    )


class Document(Base, TimestampMixin):
    """A file uploaded to a specific bot's knowledge base."""

    __tablename__ = "documents"
    __table_args__ = (Index("ix_documents_bot_status", "bot_id", "status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bot_id: Mapped[int] = mapped_column(
        ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus, name="document_status", native_enum=False, length=32),
        nullable=False,
        default=DocumentStatus.queued,
    )

    bot: Mapped[Bot] = relationship(back_populates="documents")
