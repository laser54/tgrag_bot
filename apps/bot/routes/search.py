"""Stub search endpoint compatible with future Qdrant integration."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from ..documents import document_store

router = APIRouter(prefix="/api", tags=["search"])


class SearchRequest(BaseModel):
    """Incoming semantic search payload."""

    query: str = Field(..., max_length=2000)
    limit: int = Field(5, ge=1, le=20)
    document_ids: list[str] | None = Field(
        default=None, description="Optional list of document ids to scope search."
    )

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        """Ensure the query is meaningful."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("Query cannot be empty.")
        return normalized


class SearchResult(BaseModel):
    """Single chunk returned from semantic search."""

    document_id: str
    document_name: str
    chunk_index: int
    chunk_text: str
    score: float


class SearchResponse(BaseModel):
    """Search response payload."""

    query: str
    results: list[SearchResult]
    status: Literal["stubbed"] = "stubbed"


@router.post("/search", response_model=SearchResponse)
async def semantic_search(payload: SearchRequest) -> SearchResponse:
    """Return mocked semantic search results using stored metadata."""
    records = document_store.list_documents()
    if payload.document_ids:
        allowed = set(payload.document_ids)
        records = [record for record in records if record.id in allowed]

    if not records:
        return SearchResponse(query=payload.query, results=[])

    limited = records[: payload.limit]
    results = []
    for idx, record in enumerate(limited):
        score = round(max(0.1, 0.92 - idx * 0.08), 3)
        snippet = (
            f"Excerpt from {record.name} referencing \"{payload.query[:64]}\". "
            "Real content will be returned once embeddings are wired."
        )
        results.append(
            SearchResult(
                document_id=record.id,
                document_name=record.name,
                chunk_index=0,
                chunk_text=snippet,
                score=score,
            )
        )

    return SearchResponse(query=payload.query, results=results)

