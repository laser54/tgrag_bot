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
            logging.warning(
                "TELEGRAM_BOT_TOKEN format looks unusual. " "Make sure it's correct."
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


# Global settings instance
settings = Settings()
