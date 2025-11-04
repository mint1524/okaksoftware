from __future__ import annotations

from typing import Any

import httpx

from ..config import settings


class BackendClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.backend_api_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=15.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def register_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.post("/users/register", json=payload)
        response.raise_for_status()
        return response.json()

    async def list_products(self) -> list[dict[str, Any]]:
        response = await self._client.get("/products")
        response.raise_for_status()
        return response.json().get("items", [])

    async def create_purchase(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.post("/purchases", json=payload)
        response.raise_for_status()
        return response.json()

    async def get_user_purchases(self, telegram_id: int) -> list[dict[str, Any]]:
        response = await self._client.get(f"/users/{telegram_id}/purchases")
        response.raise_for_status()
        return response.json()

    async def get_user(self, telegram_id: int) -> dict[str, Any] | None:
        response = await self._client.get(f"/users/{telegram_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

