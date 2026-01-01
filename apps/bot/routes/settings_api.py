"""API routes for runtime configuration changes."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, SecretStr, field_validator

from ..qdrant import QdrantConfig, QdrantMode, qdrant_config_store
from ..qdrant.status import get_qdrant_status

router = APIRouter(prefix="/api/settings", tags=["settings"])

QdrantModeLiteral = Literal[
    "cloud",
    "local",
    "disabled",
    "not_configured",
]


class QdrantSettingsResponse(BaseModel):
    """Payload returned to the Mini App."""

    mode: QdrantModeLiteral
    url: str | None = None
    collection: str
    status: dict


class QdrantSettingsUpdate(BaseModel):
    """Incoming payload from the Mini App."""

    mode: QdrantModeLiteral = Field(
        description="Desired Qdrant mode: cloud, local, disabled, or not_configured."
    )
    url: str | None = Field(
        default=None,
        description="Base URL for cloud/local cluster. Optional for disabled mode.",
    )
    api_key: SecretStr | None = Field(
        default=None,
        description="Qdrant API key. Required the first time cloud mode is enabled.",
    )
    collection: str | None = Field(
        default=None,
        min_length=1,
        strip_whitespace=True,
        description="Collection name. Defaults to the existing collection.",
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        """Ensure URLs are HTTP(S) when provided."""
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            return None
        if not normalized.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return normalized


def _serialize_response(
    config: QdrantConfig, status_payload: dict
) -> QdrantSettingsResponse:
    """Convert config + status to a response model."""
    return QdrantSettingsResponse(
        mode=config.mode.value,  # type: ignore[arg-type]
        url=config.public_url(),
        collection=config.collection,
        status=status_payload,
    )


@router.get("/qdrant", response_model=QdrantSettingsResponse)
async def get_qdrant_settings():
    """Return current Qdrant configuration without secrets."""
    config = qdrant_config_store.get()
    status_payload = (await get_qdrant_status(qdrant_config_store)).to_dict()
    return _serialize_response(config, status_payload)


@router.put("/qdrant", response_model=QdrantSettingsResponse)
async def update_qdrant_settings(payload: QdrantSettingsUpdate):
    """Update runtime Qdrant configuration."""
    current = qdrant_config_store.get()
    collection = payload.collection or current.collection
    submitted_url = payload.url
    mode = QdrantMode(payload.mode)

    if mode == QdrantMode.DISABLED:
        updated = QdrantConfig(mode=mode, url=None, api_key=None, collection=collection)
    elif mode == QdrantMode.NOT_CONFIGURED:
        updated = QdrantConfig(
            mode=mode,
            url=submitted_url,
            api_key=None,
            collection=collection,
        )
    elif mode == QdrantMode.LOCAL:
        url = submitted_url or current.url or "http://qdrant:6333"
        updated = QdrantConfig(mode=mode, url=url, api_key=None, collection=collection)
    elif mode == QdrantMode.CLOUD:
        url = submitted_url or current.url
        api_key = (
            payload.api_key.get_secret_value() if payload.api_key else current.api_key
        )
        if not url or not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cloud mode requires both url and api_key.",
            )
        updated = QdrantConfig(
            mode=mode, url=url, api_key=api_key, collection=collection
        )
    else:  # pragma: no cover - exhaustiveness guard
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported mode: {mode}"
        )

    qdrant_config_store.set(updated)
    status_payload = (await get_qdrant_status(qdrant_config_store)).to_dict()
    return _serialize_response(updated, status_payload)
