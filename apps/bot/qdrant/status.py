"""Helpers to gather Qdrant runtime status."""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from typing import Any

from .client import build_qdrant_client
from .config_store import QdrantConfigStore, QdrantMode


@dataclass(slots=True)
class QdrantStatusPayload:
    """Serializable payload describing current Qdrant state."""

    mode: QdrantMode
    collection: str
    reachable: bool
    collection_exists: bool
    points_count: int | None = None
    vectors_count: int | None = None
    last_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        data = asdict(self)
        data["mode"] = self.mode.value
        return data


async def get_qdrant_status(store: QdrantConfigStore) -> QdrantStatusPayload:
    """Collect status information for the current Qdrant configuration."""
    config = store.get()
    payload = QdrantStatusPayload(
        mode=config.mode,
        collection=config.collection,
        reachable=False,
        collection_exists=False,
    )

    if not config.is_active():
        if config.mode == QdrantMode.DISABLED:
            payload.last_error = "Qdrant is disabled."
        else:
            payload.last_error = "Qdrant credentials are not configured yet."
        return payload

    client = build_qdrant_client(config)
    if not client:
        payload.last_error = "Missing Qdrant URL or API key."
        return payload

    try:
        collection_exists = await asyncio.to_thread(
            client.collection_exists, config.collection
        )
        payload.collection_exists = collection_exists
        payload.reachable = True

        if collection_exists:
            description = await asyncio.to_thread(
                client.get_collection, config.collection
            )
            payload.vectors_count = getattr(description, "vectors_count", None)

            count_result = await asyncio.to_thread(
                client.count, config.collection, exact=True
            )
            payload.points_count = getattr(count_result, "count", None)

    except Exception as exc:  # pragma: no cover - depends on remote cluster
        payload.last_error = str(exc)

    return payload

