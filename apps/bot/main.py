"""Main FastAPI application with aiogram integration."""

import logging
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

# Configure logging (minimal but structured)
logging.basicConfig(level=logging.INFO)
logger.add(
    "logs/bot.log", rotation="10 MB", retention="1 week", level="INFO", encoding="utf-8"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("🚀 Starting Telegram RAG Bot")

    # Initialize bot and dispatcher for later use
    try:
        bot = Bot(token=settings.telegram_bot_token)
        dp = Dispatcher()

        # Store in app state for later access
        app.state.bot = bot
        app.state.dp = dp

        # Validate bot token by getting bot info
        try:
            bot_info = await bot.get_me()
            logger.info(f"🤖 Bot ready: @{bot_info.username} (id={bot_info.id})")
        except Exception as e:
            logger.error(f"❌ Bot token is invalid: {e}")
            logger.error("Please check your TELEGRAM_BOT_TOKEN environment variable")
            raise
        if settings.allowed_user_ids:
            logger.info(
                f"🔒 Access restricted to users: {settings.allowed_user_ids_list}"
            )
    except Exception as e:
        logger.warning(f"Bot initialization failed: {e}")
        logger.warning("Running in demo mode without Telegram bot functionality")
        app.state.bot = None
        app.state.dp = None

    # Setup webhook if URL is provided
    webhook_url = settings.webhook_url

    # If no webhook URL from env, try to read from file
    if not webhook_url:
        try:
            webhook_file = Path("/app/data/webhook_url.txt")
            if webhook_file.exists():
                webhook_url = webhook_file.read_text().strip()
                logger.info(f"🔗 Webhook URL detected: {webhook_url}")
        except Exception as e:
            logger.warning(f"Could not read webhook URL from file: {e}")

    if app.state.bot and webhook_url:
        logger.info("⚙️ Setting webhook")
        try:
            await app.state.bot.set_webhook(url=webhook_url, drop_pending_updates=True)
            logger.info("✅ Webhook configured")

            # Verify webhook was set correctly
            webhook_info = await app.state.bot.get_webhook_info()
            if webhook_info.url == webhook_url:
                logger.info(f"🧪 Webhook verified: {webhook_info.url}")
            else:
                logger.warning(
                    f"⚠️ Webhook URL mismatch. Expected: {webhook_url}, Got: {webhook_info.url}"
                )

        except Exception as e:
            logger.error(f"❌ Failed to set webhook: {e}")
            # Don't exit - webhook can be set manually later
    elif app.state.bot:
        logger.warning("No webhook URL configured - bot will not receive updates")
    else:
        logger.info("🧪 Demo mode - no Telegram bot functionality")

    # Register handlers if bot is available
    if app.state.dp:
        app.state.dp.include_router(handlers.router)
        logger.info("✅ Telegram handlers registered")
    else:
        logger.info("🧪 Demo mode - handlers not registered")

    yield

    # Shutdown
    logger.info("🛑 Shutting down bot")

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
        logger.warning("⚠️ Webhook called but bot not initialized")
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
        logger.error(f"❌ Webhook error: {e}")
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


# Removed noisy HTTP access logging middleware
