"""Document management stubs for the Mini App workflow."""

from __future__ import annotations

import logging
import math
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict

from ..documents import DocumentRecord, document_store
from ..qdrant import qdrant_config_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    """Serialized document metadata."""

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


def _serialize(record: DocumentRecord) -> DocumentResponse:
    """Convert a record into the API response schema."""
    return DocumentResponse.model_validate(record)


@router.get("/", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    """Return current documents (stubbed, in-memory)."""
    records = document_store.list_documents()
    return DocumentListResponse(items=[_serialize(record) for record in records])


@router.post(
    "/",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(file: UploadFile = File(...)) -> DocumentResponse:
    """Accept a document upload and store metadata only."""
    payload = await file.read()
    size = len(payload)
    record = document_store.add_document(file.filename, size)
    logger.info("Queued document %s (%s bytes)", record.name, record.size)
    return _serialize(record)


@router.post("/{document_id}/index", response_model=DocumentResponse)
async def index_document(document_id: str) -> DocumentResponse:
    """Mark a document as indexed (stubbed)."""
    record = document_store.get_document(document_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
        )

    config = qdrant_config_store.get()
    if not config.is_active():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Qdrant is not configured. Open the Vector Store panel and provide credentials.",
        )

    chunk_guess = max(1, math.ceil(record.size / 2000))  # Rough placeholder.
    updated = document_store.set_index_state(document_id, True, chunks=chunk_guess)
    logger.info(
        "Indexed document %s into %s (%s chunks)",
        record.name,
        config.collection,
        chunk_guess,
    )
    return _serialize(updated or record)


@router.post("/{document_id}/remove-from-index", response_model=DocumentResponse)
async def remove_from_index(document_id: str) -> DocumentResponse:
    """Mark a document as removed from the vector index."""
    record = document_store.get_document(document_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
        )
    updated = document_store.set_index_state(document_id, False, chunks=0)
    logger.info("Removed document %s from index", record.name)
    return _serialize(updated or record)


@router.delete("/{document_id}", response_model=DocumentResponse)
async def delete_document(document_id: str) -> DocumentResponse:
    """Delete uploaded document metadata."""
    record = document_store.delete_document(document_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
        )
    logger.info("Deleted document %s", record.name)
    return _serialize(record)

