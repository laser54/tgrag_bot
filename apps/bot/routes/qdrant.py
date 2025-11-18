"""Routes exposing Qdrant status information."""

from fastapi import APIRouter

from ..qdrant import qdrant_config_store
from ..qdrant.status import get_qdrant_status

router = APIRouter(prefix="/qdrant", tags=["qdrant"])


@router.get("/status")
async def qdrant_status():
    """Return the current Qdrant connectivity state."""
    payload = await get_qdrant_status(qdrant_config_store)
    return payload.to_dict()

