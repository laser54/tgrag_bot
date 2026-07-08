"""Repository for the `documents` table."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Document, DocumentStatus


class DocumentsRepository:
    """Async data access for uploaded documents."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def list_all(self) -> list[Document]:
        """Return documents sorted by creation time (newest first)."""
        result = await self._s.execute(
            select(Document).order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, document_id: int) -> Document | None:
        return await self._s.get(Document, document_id)

    async def create(
        self,
        *,
        filename: str,
        size: int,
        bot_id: int | None = None,
        status: DocumentStatus = DocumentStatus.queued,
    ) -> Document:
        """Persist a new document metadata row."""
        doc = Document(
            filename=filename,
            size=size,
            bot_id=bot_id,
            status=status,
        )
        self._s.add(doc)
        await self._s.commit()
        await self._s.refresh(doc)
        return doc

    async def update_status(
        self,
        document_id: int,
        status: DocumentStatus,
        *,
        chunk_count: int | None = None,
        error: str | None = None,
        indexed_at: datetime | None = None,
    ) -> Document | None:
        """Transition a document's lifecycle status and related fields."""
        doc = await self._s.get(Document, document_id)
        if doc is None:
            return None
        doc.status = status
        if chunk_count is not None:
            doc.chunk_count = chunk_count
        if error is not None:
            doc.error = error
        if indexed_at is not None:
            doc.indexed_at = indexed_at
        await self._s.commit()
        await self._s.refresh(doc)
        return doc

    async def delete(self, document_id: int) -> Document | None:
        """Remove a document row. Returns the deleted row or None if missing."""
        doc = await self._s.get(Document, document_id)
        if doc is None:
            return None
        await self._s.delete(doc)
        await self._s.commit()
        return doc
