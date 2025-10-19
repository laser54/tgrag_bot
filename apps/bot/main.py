"""Main FastAPI application with aiogram integration."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from aiogram import Bot, Dispatcher
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from .routes.health import router as health_router
from .settings import settings
from .tg import handlers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger.add(
    "logs/bot.log", rotation="10 MB", retention="1 week", level="INFO", encoding="utf-8"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("Starting Telegram RAG Bot...")

    # Initialize bot and dispatcher for later use
    try:
        bot = Bot(token=settings.telegram_bot_token)
        dp = Dispatcher()

        # Store in app state for later access
        app.state.bot = bot
        app.state.dp = dp

        logger.info(f"Bot configured for token: {settings.telegram_bot_token[:10]}...")
        if settings.allowed_user_ids:
            logger.info(f"Restricted to users: {settings.allowed_user_ids_list}")
    except Exception as e:
        logger.warning(f"Bot initialization failed: {e}")
        logger.warning("Running in demo mode without Telegram bot functionality")
        app.state.bot = None
        app.state.dp = None

    # Setup webhook if URL is provided (by cloudflared tunnel)
    # In Docker mode, we run in polling mode for simplicity
    if app.state.bot and settings.webhook_url and not os.getenv("DOCKER_CONTAINER"):
        logger.info(f"Setting up webhook: {settings.webhook_url}")
        try:
            await app.state.bot.set_webhook(
                url=settings.webhook_url, drop_pending_updates=True
            )
            logger.info("✅ Webhook configured successfully")
        except Exception as e:
            logger.error(f"❌ Failed to set webhook: {e}")
            # Don't exit - webhook can be set manually later
    elif app.state.bot:
        logger.info("Running in polling mode (Docker or no webhook URL)")
    else:
        logger.info("Demo mode - no Telegram bot functionality")

    # Register handlers if bot is available
    if app.state.dp:
        app.state.dp.include_router(handlers.router)
        logger.info("✅ Telegram handlers registered")
    else:
        logger.info("Demo mode - handlers not registered")

    # Start polling in Docker mode
    if os.getenv("DOCKER_CONTAINER") and app.state.bot and app.state.dp:
        logger.info("🚀 Starting bot polling...")
        polling_task = asyncio.create_task(app.state.dp.start_polling(app.state.bot))
    else:
        polling_task = None

    yield

    # Stop polling if running
    if polling_task:
        logger.info("🛑 Stopping bot polling...")
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass

    # Shutdown
    logger.info("Shutting down bot...")

    # Remove webhook if it was set
    if app.state.bot and settings.webhook_url:
        try:
            await app.state.bot.delete_webhook()
            logger.info("✅ Webhook removed")
        except Exception as e:
            logger.warning(f"Failed to remove webhook: {e}")

    if app.state.bot:
        await app.state.bot.session.close()


# Create FastAPI app
app = FastAPI(
    title="Telegram RAG Bot",
    description="Telegram bot with RAG memory for document Q&A",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook updates."""
    if not app.state.bot or not app.state.dp:
        return {"status": "error", "message": "Bot not initialized (demo mode)"}

    try:
        # Get update data
        update_data = await request.json()

        # Process update with aiogram
        from aiogram.types import Update

        update = Update(**update_data)

        # Handle the update
        await app.state.dp.feed_update(bot=app.state.bot, update=update)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}


# Mount static files for webapp
webapp_path = Path(__file__).parent.parent.parent / "webapp"
if webapp_path.exists():
    app.mount("/webapp", StaticFiles(directory=str(webapp_path)), name="webapp")
    logger.info(f"Mounted webapp static files at: {webapp_path}")
else:
    logger.warning(f"Webapp directory not found: {webapp_path}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Telegram RAG Bot API",
        "docs": "/docs",
        "health": "/health",
        "webapp": "/webapp/",
    }


# Middleware to log requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    return response
