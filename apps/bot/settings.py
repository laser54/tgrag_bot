"""Application settings with Pydantic validation."""

import logging

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    allowed_user_ids: str | None = Field(None, env="ALLOWED_USER_IDS")
    port: int = Field(8080, env="PORT")
    webapp_url: str = Field("http://localhost:8080/webapp/", env="WEBAPP_URL")
    webhook_url: str | None = Field(None, env="WEBHOOK_URL")

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"

    @validator("telegram_bot_token")
    def validate_telegram_token(cls, v):
        """Validate Telegram bot token format."""
        if not v or not v.strip():
            raise ValueError(
                "TELEGRAM_BOT_TOKEN is required. " "Get it from @BotFather on Telegram."
            )
        if not v.startswith(("123456:ABC-", "123456789:ABC-")):
            logging.getLogger(__name__).debug(
                "TELEGRAM_BOT_TOKEN format looks unusual; continuing."
            )
        return v.strip()

    @property
    def allowed_user_ids_list(self) -> list[int]:
        """Get allowed user IDs as a list of integers."""
        if not self.allowed_user_ids:
            return []
        return [
            int(uid.strip()) for uid in self.allowed_user_ids.split(",") if uid.strip()
        ]

    @property
    def webapp_base_url(self) -> str:
        """Get the base HTTPS URL for webapp based on webhook URL."""
        if self.webhook_url and self.webhook_url.startswith("https://"):
            # Extract base URL: https://domain/webhook/telegram -> https://domain
            base_url = self.webhook_url.replace("/webhook/telegram", "")
            return base_url
        # Fallback for development
        return "https://example.trycloudflare.com"

    @property
    def webapp_url_full(self) -> str:
        """Get the full webapp URL with /webapp/ path."""
        return f"{self.webapp_base_url}/webapp/"


# Global settings instance
settings = Settings()
