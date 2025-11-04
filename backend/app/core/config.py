from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="OKAK_", extra="ignore")

    project_name: str = "OKAK Software Platform"
    api_prefix: str = "/api"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    database_url: AnyUrl = Field(
        default="postgresql+asyncpg://okak:okak@db:5432/okak",
        description="SQLAlchemy connection string for async engine.",
    )
    database_echo: bool = False

    token_ttl_days: int = 7
    support_username: str | None = None

    domain_gpt: str = "gpt.kcbot.ru"
    domain_vpn: str = "vpn.kcbot.ru"

    yoomoney_shop_id: str = Field(default="", description="YooMoney shop identifier")
    yoomoney_secret_key: str = Field(default="", description="YooMoney secret key")
    yoomoney_webhook_secret: str = Field(default="", description="Shared secret for webhook validation")
    yoomoney_api_base_url: AnyUrl | None = Field(default="https://api.yookassa.ru/v3")
    yoomoney_return_url: AnyUrl | None = None

    scheduler_enabled: bool = True
    cleanup_cron: str = "0 * * * *"  # every hour

    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])

    log_level: Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    admin_password_hash: str = Field(default="", description="Bcrypt hash for admin panel access")
    admin_jwt_secret: str = Field(default="change_me", description="Secret key for admin JWT tokens")
    admin_token_expire_minutes: int = 60


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
