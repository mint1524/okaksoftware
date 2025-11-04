from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import httpx

from ..core.config import Settings, get_settings


@dataclass
class YooMoneyPayment:
    payment_id: str
    confirmation_url: str | None
    status: str
    raw: dict[str, Any]


class YooMoneyClient:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._client: httpx.AsyncClient | None = None

    async def _client_instance(self) -> httpx.AsyncClient:
        if not self._client:
            base_url = self.settings.yoomoney_api_base_url or "https://api.yookassa.ru/v3"
            self._client = httpx.AsyncClient(base_url=str(base_url), timeout=20.0)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _auth_header(self) -> str:
        creds = f"{self.settings.yoomoney_shop_id}:{self.settings.yoomoney_secret_key}".encode("utf-8")
        return base64.b64encode(creds).decode("utf-8")

    async def create_payment(
        self,
        amount: float,
        currency: str,
        description: str,
        metadata: dict[str, Any] | None = None,
        return_url: str | None = None,
    ) -> YooMoneyPayment:
        if not self.settings.yoomoney_shop_id or not self.settings.yoomoney_secret_key:
            raise RuntimeError("YooMoney credentials are not configured")

        client = await self._client_instance()
        headers = {
            "Authorization": f"Basic {self._auth_header()}",
            "Content-Type": "application/json",
            "Idempotence-Key": str(uuid4()),
        }
        payload: dict[str, Any] = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": currency,
            },
            "capture": True,
            "description": description[:128],
        }
        if return_url:
            payload["confirmation"] = {
                "type": "redirect",
                "return_url": return_url,
            }
        if metadata:
            payload["metadata"] = metadata

        response = await client.post("/payments", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        confirmation_url = None
        confirmation = data.get("confirmation")
        if isinstance(confirmation, dict):
            confirmation_url = confirmation.get("confirmation_url") or confirmation.get("url")
        return YooMoneyPayment(
            payment_id=data.get("id"),
            confirmation_url=confirmation_url,
            status=data.get("status"),
            raw=data,
        )


async def get_yoomoney_client() -> YooMoneyClient:
    return YooMoneyClient()
