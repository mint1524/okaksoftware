from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any

import httpx

from ..core.config import Settings, get_settings


@dataclass
class InvoiceResult:
    order_id: str
    invoice_url: str
    payload: dict[str, Any]


class DigisellerClient:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._client: httpx.AsyncClient | None = None

    async def _client_instance(self) -> httpx.AsyncClient:
        if not self._client:
            self._client = httpx.AsyncClient(base_url=self.settings.digiseller_base_url.unicode_string(), timeout=15.0)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def create_invoice(self, product_id: str, quantity: int = 1) -> InvoiceResult:
        if not self.settings.digiseller_api_key or not self.settings.digiseller_seller_id:
            raise RuntimeError("Digiseller credentials are not configured")

        payload = {
            "seller_id": self.settings.digiseller_seller_id,
            "product_id": product_id,
            "quantity": quantity,
        }

        client = await self._client_instance()
        response = await client.post("/api/purchases", json=payload, headers=self._headers())
        response.raise_for_status()
        data = response.json()
        order_id = str(data.get("order_id") or data.get("invoice_id") or "")
        invoice_url = data.get("payment_url") or data.get("invoice_url")
        if not order_id or not invoice_url:
            raise RuntimeError("Unexpected response from Digiseller when creating invoice")
        return InvoiceResult(order_id=order_id, invoice_url=invoice_url, payload=data)

    async def get_invoice(self, order_id: str) -> dict[str, Any]:
        if not self.settings.digiseller_api_key or not self.settings.digiseller_seller_id:
            raise RuntimeError("Digiseller credentials are not configured")

        client = await self._client_instance()
        response = await client.get(f"/api/purchases/{order_id}", headers=self._headers())
        response.raise_for_status()
        return response.json()

    @staticmethod
    def verify_signature(secret: str, signature: str, payload: dict[str, Any]) -> bool:
        digest = hmac.new(secret.encode("utf-8"), json.dumps(payload, separators=(",", ":")).encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(digest, signature)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.digiseller_api_key}",
            "Accept": "application/json",
        }


async def get_digiseller_client() -> DigisellerClient:
    return DigisellerClient()
