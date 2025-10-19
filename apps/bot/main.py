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
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()

    # Store in app state for later access
    app.state.bot = bot
    app.state.dp = dp

    logger.info(f"Bot configured for token: {settings.telegram_bot_token[:10]}...")
    if settings.allowed_user_ids:
        logger.info(f"Restricted to users: {settings.allowed_user_ids_list}")

    yield

    # Shutdown
    logger.info("Shutting down bot...")
    await bot.session.close()


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
