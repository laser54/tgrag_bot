"""Main FastAPI application with aiogram integration."""

import asyncio
import logging
import socket
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from aiogram import Bot, Dispatcher
from aiogram.types import MenuButtonWebApp, WebAppInfo
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from .db import init_db, shutdown_db
from .routes.bots import router as bots_router
from .routes.documents import router as documents_router
from .routes.health import router as health_router
from .routes.qdrant import router as qdrant_router
from .routes.search import router as search_router
from .routes.settings_api import router as settings_router
from .routes.webhook import router as webhook_router
from .settings import settings
from .tg import handlers
from .tg.bot_registry import bot_registry

# Configure logging (minimal but structured)
logging.basicConfig(level=logging.INFO)
logger.add(
    "logs/bot.log", rotation="10 MB", retention="1 week", level="INFO", encoding="utf-8"
)


async def _resolve_dns(host: str, timeout: float = 3.0) -> str | None:
    """Try to resolve `host` via the default resolver. Returns IP or None."""
    loop = asyncio.get_running_loop()
    try:
        infos = await asyncio.wait_for(
            loop.getaddrinfo(host, 443, type=socket.SOCK_STREAM), timeout=timeout
        )
        return infos[0][4][0] if infos else None
    except Exception:
        return None


async def _setup_webhook_with_backoff(bot: Bot, webhook_url: str) -> bool:
    """Robust webhook registration for flaky tunnels (Pinggy free, first-launch
    Cloudflared, etc.).

    - Waits for public DNS to resolve the tunnel host (up to ~5 min).
    - Exponential backoff on `setWebhook` errors.
    - Does NOT drop pending updates (so user's /start presses survive).
    - Emits actionable diagnostics on final failure.
    """
    host = urlparse(webhook_url).hostname or ""
    logger.info(f"⚙️ Setting webhook → {webhook_url}")

    dns_deadline = 120  # seconds to wait for DNS propagation
    dns_waited = 0
    while dns_waited < dns_deadline:
        ip = await _resolve_dns(host)
        if ip is not None:
            logger.info(f"🌐 DNS OK: {host} -> {ip}")
            break
        logger.warning(
            f"🟡 DNS not resolving yet for {host} (waited {dns_waited}s) — "
            "waiting for tunnel propagation"
        )
        await asyncio.sleep(5)
        dns_waited += 5
    else:
        logger.error(
            f"❌ DNS never resolved for {host} after {dns_deadline}s. "
            "Pinggy free occasionally allocates subdomains that don't "
            "propagate to public DNS — Telegram will also fail to reach it. "
            "Fix: `docker compose restart pinggy bot` to get a fresh URL, or "
            "add PINGGY_TOKEN to .env for a stable *.a.pinggy.online host. "
            "Bot stays up; once the tunnel is reachable, call "
            "POST /admin/webhook/refresh to re-register without restart."
        )
        return False

    delays = [2, 4, 8, 16, 30, 60, 60, 60]  # ~4 min of retries
    for attempt, delay in enumerate(delays, start=1):
        try:
            await bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=False,
                allowed_updates=["message", "callback_query", "edited_message"],
            )
            info = await bot.get_webhook_info()
            if info.url == webhook_url:
                logger.info(f"✅ Webhook verified: {info.url}")
                return True
            logger.warning(
                f"⚠️ Webhook URL mismatch. expected={webhook_url} got={info.url!r}"
            )
        except Exception as exc:
            logger.error(f"❌ setWebhook attempt {attempt}/{len(delays)} failed: {exc}")

        if attempt < len(delays):
            logger.info(f"Retrying in {delay}s...")
            await asyncio.sleep(delay)

    logger.error(
        "Webhook setup exhausted all retries. Bot will keep running; "
        "POST /admin/webhook/refresh once the tunnel is reachable."
    )
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("🚀 Starting Telegram RAG Bot")

    # Initialize database (dev: create_all; Alembic migrations coming next)
    try:
        await init_db()
    except Exception as exc:
        logger.error(f"❌ Database init failed: {exc}")
        raise

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

    webapp_url_full: str | None = None
    if webhook_url:
        settings.webhook_url = webhook_url
        base_url = webhook_url.removesuffix("/webhook/telegram")
        base_url = base_url.rstrip("/")
        webapp_url_full = f"{base_url}/webapp/"
        settings.webapp_url = webapp_url_full
        try:
            webapp_file = Path("/app/data/webapp_url.txt")
            webapp_file.write_text(webapp_url_full)
        except Exception as exc:
            logger.debug(f"Could not cache webapp URL: {exc}")
        logger.info(f"🌐 WebApp URL resolved: {webapp_url_full}")
        app.state.webapp_url = webapp_url_full

    if app.state.bot and webhook_url:
        await _setup_webhook_with_backoff(app.state.bot, webhook_url)
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

    # Configure default menu button with WebApp access
    if app.state.bot:
        target_webapp_url = (
            getattr(app.state, "webapp_url", None)
            or settings.webapp_url_full
            or settings.webapp_url
        )
        try:
            await app.state.bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="Document Hub",
                    web_app=WebAppInfo(url=target_webapp_url),
                )
            )
            logger.info("✅ Chat menu button configured with WebApp")
        except Exception as exc:
            logger.warning(f"Could not set chat menu button: {exc}")

    # Final ready message
    if app.state.bot and webhook_url:
        logger.info("🎯 Bot is fully operational and ready to receive messages")
    elif app.state.bot:
        logger.warning(
            "⚠️ Bot initialized but webhook not configured - manual polling required"
        )
    else:
        logger.info("🧪 Running in demo mode - Telegram functionality disabled")

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

    await bot_registry.shutdown_all()
    await shutdown_db()


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
app.include_router(qdrant_router)
app.include_router(documents_router)
app.include_router(settings_router)
app.include_router(search_router)
app.include_router(bots_router)
app.include_router(webhook_router)


@app.get("/admin/webhook/info")
async def admin_webhook_info():
    """Current webhook status reported by Telegram (main manager bot)."""
    if not app.state.bot:
        return {"status": "error", "message": "Bot not initialized"}
    try:
        info = await app.state.bot.get_webhook_info()
        return {
            "configured_url": settings.webhook_url,
            "telegram_url": info.url,
            "pending_update_count": info.pending_update_count,
            "last_error_date": info.last_error_date,
            "last_error_message": info.last_error_message,
            "allowed_updates": info.allowed_updates,
        }
    except Exception as exc:
        logger.error(f"getWebhookInfo failed: {exc}")
        return {"status": "error", "message": str(exc)}


@app.post("/admin/webhook/refresh")
async def admin_webhook_refresh(request: Request):
    """Re-register the main bot's webhook using `settings.webhook_url`.

    Useful when the tunnel DNS propagated late, or the tunnel URL changed
    without a bot restart. Optional JSON body: `{"url": "https://..."}` to
    override the configured URL for this call.
    """
    if not app.state.bot:
        return {"status": "error", "message": "Bot not initialized"}
    try:
        body = await request.json()
    except Exception:
        body = {}
    target = body.get("url") or settings.webhook_url
    if not target:
        return {
            "status": "error",
            "message": "No webhook URL configured and none provided in body",
        }
    ok = await _setup_webhook_with_backoff(app.state.bot, target)
    info = await app.state.bot.get_webhook_info()
    return {
        "status": "ok" if ok else "partial",
        "requested": target,
        "telegram_url": info.url,
        "pending_update_count": info.pending_update_count,
        "last_error_message": info.last_error_message,
    }


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook updates."""
    if not app.state.bot or not app.state.dp:
        logger.warning("⚠️ Webhook called but bot not initialized")
        return {"status": "error", "message": "Bot not initialized (demo mode)"}

    try:
        # Get update data
        update_data = await request.json()
        update_id = update_data.get("update_id", "unknown")
        logger.debug(f"Received webhook update {update_id}")

        # Process update with aiogram
        from aiogram.types import Update

        update = Update(**update_data)

        # Handle the update
        await app.state.dp.feed_update(bot=app.state.bot, update=update)
        logger.debug(f"Processed webhook update {update_id}")
        return {"status": "ok"}

    except Exception as e:
        logger.error(f"❌ Webhook error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


# Mount static files for webapp
webapp_path = Path(__file__).parent.parent.parent / "webapp"
if webapp_path.exists():
    app.mount(
        "/webapp",
        StaticFiles(directory=str(webapp_path), html=True),
        name="webapp",
    )
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
