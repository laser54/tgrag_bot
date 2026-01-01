"""Runtime configuration helpers for Qdrant connectivity."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from threading import RLock
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from ..settings import Settings


class QdrantMode(str, Enum):
    """Qdrant connectivity modes supported by the application."""

    NOT_CONFIGURED = "not_configured"
    DISABLED = "disabled"
    LOCAL = "local"
    CLOUD = "cloud"


@dataclass(slots=True)
class QdrantConfig:
    """In-memory representation of the effective Qdrant configuration."""

    mode: QdrantMode = QdrantMode.NOT_CONFIGURED
    url: str | None = None
    api_key: str | None = None
    collection: str = "tgrag-bot"

    def is_active(self) -> bool:
        """Return True when the configuration should attempt to connect."""
        return self.mode in (QdrantMode.LOCAL, QdrantMode.CLOUD)

    def public_url(self) -> str | None:
        """Return a sanitized URL without credentials for UI display."""
        if not self.url:
            return None
        parts = urlsplit(self.url)
        if not parts.scheme or not parts.hostname:
            return self.url
        host = parts.hostname
        if parts.port:
            host = f"{host}:{parts.port}"
        return f"{parts.scheme}://{host}"


class QdrantConfigStore:
    """Thread-safe storage for runtime Qdrant configuration."""

    def __init__(self, initial: QdrantConfig):
        self._lock = RLock()
        self._config = initial

    def get(self) -> QdrantConfig:
        """Return a copy of the current configuration."""
        with self._lock:
            return replace(self._config)

    def set(self, config: QdrantConfig) -> QdrantConfig:
        """Replace the stored configuration."""
        with self._lock:
            self._config = config
            return replace(self._config)

    def update(self, **kwargs) -> QdrantConfig:
        """Update individual fields in the configuration."""
        with self._lock:
            self._config = replace(self._config, **kwargs)
            return replace(self._config)


def build_initial_config(app_settings: Settings) -> QdrantConfig:
    """Create the initial Qdrant configuration from BaseSettings."""
    collection = app_settings.qdrant_collection

    if app_settings.use_local_qdrant:
        url = app_settings.qdrant_url or "http://qdrant:6333"
        return QdrantConfig(
            mode=QdrantMode.LOCAL,
            url=url,
            api_key=None,
            collection=collection,
        )

    if app_settings.qdrant_url and app_settings.qdrant_api_key:
        return QdrantConfig(
            mode=QdrantMode.CLOUD,
            url=app_settings.qdrant_url,
            api_key=app_settings.qdrant_api_key,
            collection=collection,
        )

    if app_settings.qdrant_url and not app_settings.qdrant_api_key:
        # URL without credentials usually means the user still needs to finish setup.
        return QdrantConfig(
            mode=QdrantMode.NOT_CONFIGURED,
            url=app_settings.qdrant_url,
            api_key=None,
            collection=collection,
        )

    return QdrantConfig(
        mode=QdrantMode.NOT_CONFIGURED,
        url=None,
        api_key=None,
        collection=collection,
    )
