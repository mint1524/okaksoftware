from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from ..core.config import Settings, get_settings


class TokenManager:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def generate_token(self) -> str:
        return secrets.token_urlsafe(32)

    def expires_at(self, days: int | None = None) -> datetime:
        ttl_days = days or self.settings.token_ttl_days
        return datetime.now(timezone.utc) + timedelta(days=ttl_days)

    def domain_for_type(self, product_type: str) -> str:
        mapping = {
            "gpt": self.settings.domain_gpt,
            "vpn": self.settings.domain_vpn,
        }
        return mapping.get(product_type, self.settings.domain_gpt)

    def build_link(self, domain: str, token: str) -> str:
        return f"https://{domain}/{token}"
