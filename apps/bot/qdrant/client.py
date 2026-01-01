"""Factory helpers for connecting to Qdrant."""

from __future__ import annotations

from qdrant_client import QdrantClient

from .config_store import QdrantConfig, QdrantMode


def build_qdrant_client(config: QdrantConfig) -> QdrantClient | None:
    """Return a configured Qdrant client or None when disabled."""
    if not config.is_active():
        return None

    if config.mode == QdrantMode.LOCAL:
        url = config.url or "http://qdrant:6333"
        return QdrantClient(url=url)

    if config.mode == QdrantMode.CLOUD:
        if not config.url or not config.api_key:
            return None
        return QdrantClient(url=config.url, api_key=config.api_key)

    return None
