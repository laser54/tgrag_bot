"""Thread-safe in-memory storage for uploaded document metadata."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from threading import RLock
from uuid import uuid4


@dataclass(slots=True)
class DocumentRecord:
    """Represents a single uploaded document."""

    id: str
    name: str
    size: int
    uploaded_at: datetime
    indexed: bool = False
    chunks: int = 0


class DocumentStore:
    """Simple in-memory store suitable for local development stubs."""

    def __init__(self):
        self._lock = RLock()
        self._records: dict[str, DocumentRecord] = {}

    def list_documents(self) -> list[DocumentRecord]:
        """Return documents sorted by upload time (newest first)."""
        with self._lock:
            items = [replace(record) for record in self._records.values()]
        items.sort(key=lambda record: record.uploaded_at, reverse=True)
        return items

    def add_document(self, name: str, size: int) -> DocumentRecord:
        """Add a new document record."""
        record = DocumentRecord(
            id=str(uuid4()),
            name=name,
            size=size,
            uploaded_at=datetime.utcnow(),
        )
        with self._lock:
            self._records[record.id] = record
        return replace(record)

    def get_document(self, document_id: str) -> DocumentRecord | None:
        """Return a document by identifier."""
        with self._lock:
            record = self._records.get(document_id)
            return replace(record) if record else None

    def delete_document(self, document_id: str) -> DocumentRecord | None:
        """Remove a document from the store."""
        with self._lock:
            record = self._records.pop(document_id, None)
            return replace(record) if record else None

    def set_index_state(
        self, document_id: str, indexed: bool, chunks: int | None = None
    ) -> DocumentRecord | None:
        """Update indexing metadata for a document."""
        with self._lock:
            record = self._records.get(document_id)
            if not record:
                return None
            record.indexed = indexed
            if chunks is not None:
                record.chunks = chunks
            elif not indexed:
                record.chunks = 0
            return replace(record)


document_store = DocumentStore()

