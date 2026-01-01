"""Thread-safe in-memory storage for uploaded document metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
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

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "size": self.size,
            "uploaded_at": self.uploaded_at.isoformat(),
            "indexed": self.indexed,
            "chunks": self.chunks,
        }

    @classmethod
    def from_dict(cls, data: dict) -> DocumentRecord:
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            size=data["size"],
            uploaded_at=datetime.fromisoformat(data["uploaded_at"]),
            indexed=data.get("indexed", False),
            chunks=data.get("chunks", 0),
        )


class DocumentStore:
    """Thread-safe persistent store for document metadata."""

    def __init__(self, storage_path: str = "data/documents.json"):
        self._lock = RLock()
        self._storage_path = Path(storage_path)
        self._records: dict[str, DocumentRecord] = {}
        self._load_from_disk()

    def _load_from_disk(self):
        """Load records from JSON file."""
        if not self._storage_path.exists():
            return

        try:
            with open(self._storage_path, encoding="utf-8") as f:
                data = json.load(f)
                with self._lock:
                    self._records = {
                        item["id"]: DocumentRecord.from_dict(item) for item in data
                    }
        except Exception as e:
            # If load fails, we start empty but log it (print for now as logger not injected)
            print(f"Failed to load document store: {e}")

    def _save_to_disk(self):
        """Save records to JSON file."""
        try:
            # Ensure directory exists
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)

            with self._lock:
                data = [record.to_dict() for record in self._records.values()]

            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save document store: {e}")

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
            self._save_to_disk()
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
            if record:
                self._save_to_disk()
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
            self._save_to_disk()
            return replace(record)


# Initialize with data/documents.json which maps to host ./data/documents.json
document_store = DocumentStore("data/documents.json")
