from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="OKAK_")

    telegram_bot_token: str
    backend_api_url: str = "http://backend:8000/api"
    support_username: str | None = None


settings = BotSettings()
