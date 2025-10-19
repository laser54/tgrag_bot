"""Health check endpoint."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health_check():
    """Return application health status."""
    return {"status": "ok"}


@router.get("/status")
async def bot_status(request: Request):
    """Bot and webhook status check."""
    app = request.app
    status = {
        "bot_initialized": False,
        "webhook_configured": False,
        "webhook_url": None,
        "bot_info": None,
    }

    if hasattr(app.state, "bot") and app.state.bot:
        status["bot_initialized"] = True
        try:
            bot_info = await app.state.bot.get_me()
            status["bot_info"] = {
                "id": bot_info.id,
                "username": bot_info.username,
                "first_name": bot_info.first_name,
            }
        except Exception as e:
            status["bot_error"] = str(e)

        try:
            webhook_info = await app.state.bot.get_webhook_info()
            status["webhook_configured"] = webhook_info.url is not None
            status["webhook_url"] = webhook_info.url
            status["webhook_pending_updates"] = webhook_info.pending_update_count
        except Exception as e:
            status["webhook_error"] = str(e)

    return status
