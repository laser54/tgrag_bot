"""Document management endpoints backed by the SQLite data layer.

The response schema is preserved for the Mini App: ``id`` is exposed as a
string (the ORM key is an int) and ``indexed``/``chunks`` are derived from the
document lifecycle status so the ORM stays the single source of truth.

Indexing itself is still a placeholder (real ingestion lands in task B1); these
endpoints only flip persisted status/chunk metadata.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict

from ..db import get_session
from ..db.models import DocumentStatus
from ..db.repositories import DocumentsRepository
from ..qdrant import qdrant_config_store
from ..settings import settings

router = APIRouter(prefix="/api/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    """Serialized document metadata (API contract kept stable for the Mini App)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    size: int
    uploaded_at: datetime
    indexed: bool
    chunks: int


class DocumentListResponse(BaseModel):
    """List payload for documents."""

    items: list[DocumentResponse]


def _serialize(doc) -> DocumentResponse:
    """Convert an ORM ``Document`` into the stable API response schema."""
    return DocumentResponse(
        id=str(doc.id),
        name=doc.filename,
        size=doc.size,
        uploaded_at=doc.created_at,
        indexed=doc.status == DocumentStatus.ready,
        chunks=doc.chunk_count,
    )


def _parse_doc_id(document_id: str) -> int:
    """Parse the string id from the URL into the ORM int key."""
    try:
        return int(document_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        ) from exc


@router.get("/", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    """Return all documents (newest first)."""
    async with get_session() as session:
        repo = DocumentsRepository(session)
        docs = await repo.list_all()
        return DocumentListResponse(items=[_serialize(d) for d in docs])


@router.post(
    "/",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(file: UploadFile = File(...)) -> DocumentResponse:
    """Accept a document upload and persist metadata.

    ``bot_id`` is left NULL until Mini App auth (task A2) provides the acting
    bot; vectors do not exist yet so no cross-tenant leak is possible.
    """
    payload = await file.read()
    size = len(payload)

    max_size_bytes = settings.max_file_size_mb * 1024 * 1024
    if size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size is {settings.max_file_size_mb}MB.",
        )

    filename = file.filename or "untitled"

    async with get_session() as session:
        repo = DocumentsRepository(session)
        doc = await repo.create(filename=filename, size=size)

        # Save file to disk; roll back the metadata row on failure.
        try:
            upload_dir = Path(settings.upload_dir)
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / f"{doc.id}_{filename}"
            file_path.write_bytes(payload)
        except Exception as exc:
            await repo.delete(doc.id)
            raise HTTPException(
                status_code=500, detail="Failed to save file to disk."
            ) from exc

        # Re-read after potential refresh to return consistent data.
        refreshed = await repo.get_by_id(doc.id)
        return _serialize(refreshed or doc)


@router.post("/{document_id}/index", response_model=DocumentResponse)
async def index_document(document_id: str) -> DocumentResponse:
    """Mark a document as indexed (placeholder until real ingestion in B1)."""
    doc_id = _parse_doc_id(document_id)

    config = qdrant_config_store.get()
    if not config.is_active():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Qdrant is not configured. Open the Vector Store panel and provide credentials.",
        )

    async with get_session() as session:
        repo = DocumentsRepository(session)
        doc = await repo.get_by_id(doc_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
            )

        chunk_guess = max(1, math.ceil(doc.size / 2000))  # Placeholder until B1.
        updated = await repo.update_status(
            doc_id,
            DocumentStatus.ready,
            chunk_count=chunk_guess,
            indexed_at=datetime.now(UTC),
        )
        return _serialize(updated or doc)


@router.post("/{document_id}/remove-from-index", response_model=DocumentResponse)
async def remove_from_index(document_id: str) -> DocumentResponse:
    """Mark a document as removed from the vector index."""
    doc_id = _parse_doc_id(document_id)
    async with get_session() as session:
        repo = DocumentsRepository(session)
        doc = await repo.get_by_id(doc_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
            )
        updated = await repo.update_status(
            doc_id,
            DocumentStatus.queued,
            chunk_count=0,
            indexed_at=None,
        )
        return _serialize(updated or doc)


@router.delete("/{document_id}", response_model=DocumentResponse)
async def delete_document(document_id: str) -> DocumentResponse:
    """Delete an uploaded document (metadata + file on disk)."""
    doc_id = _parse_doc_id(document_id)
    async with get_session() as session:
        repo = DocumentsRepository(session)
        doc = await repo.get_by_id(doc_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
            )
        deleted = await repo.delete(doc_id)

    # Best-effort file cleanup; metadata is already gone.
    try:
        upload_dir = Path(settings.upload_dir)
        file_path = upload_dir / f"{doc.id}_{doc.filename}"
        if file_path.exists():
            file_path.unlink()
    except Exception as exc:  # noqa: BLE001
        import logging

        logging.getLogger(__name__).warning(f"Failed to delete file {doc.id}: {exc}")

    return _serialize(deleted or doc)
