from __future__ import annotations

import asyncio
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode
from uuid import uuid4

import httpx

from ..core.config import Settings, get_settings

QUICKPAY_URL = "https://yoomoney.ru/quickpay/confirm.xml"


@dataclass
class WalletPaymentStatus:
    success: bool
    operation_id: str | None = None
    amount: float | None = None
    currency: str | None = None
    raw: dict[str, Any] | None = None


class YooMoneyWalletClient:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._client: httpx.AsyncClient | None = None
        self._lock = asyncio.Lock()

    async def _client_instance(self) -> httpx.AsyncClient:
        if not self._client:
            self._client = httpx.AsyncClient(base_url="https://yoomoney.ru/api", timeout=20.0)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def build_payment_link(
        self,
        amount: float,
        label: str,
        description: str,
        success_url: str | None = None,
        payment_type: str = "AC",
    ) -> str:
        if not self.settings.yoomoney_wallet_account:
            raise RuntimeError("YooMoney wallet account is not configured")
        params = {
            "receiver": self.settings.yoomoney_wallet_account,
            "quickpay-form": "shop",
            "paymentType": payment_type,
            "sum": f"{amount:.2f}",
            "label": label,
            "targets": description[:150],
            "formcomment": description[:150],
            "short-dest": description[:100],
        }
        if success_url:
            params["successURL"] = success_url
        return f"{QUICKPAY_URL}?{urlencode(params)}"

    async def fetch_operations(self, label: str) -> list[dict[str, Any]]:
        if not self.settings.yoomoney_wallet_access_token:
            raise RuntimeError("YooMoney wallet access token is not configured")
        client = await self._client_instance()
        headers = {
            "Authorization": f"Bearer {self.settings.yoomoney_wallet_access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "label": label,
            "records": 20,
            "details": "true",
        }
        response = await client.post("/operation-history", headers=headers, data=data)
        response.raise_for_status()
        payload = response.json()
        operations = payload.get("operations")
        if not isinstance(operations, list):
            return []
        return operations

    async def check_payment(self, label: str, expected_amount: float | None = None) -> WalletPaymentStatus:
        operations = await self.fetch_operations(label)
        for op in operations:
            if op.get("label") != label:
                continue
            if op.get("direction") not in {"in"}:
                continue
            if op.get("status") not in {"success", "done"}:
                continue
            amount_value = op.get("amount")
            try:
                amount = float(amount_value) if amount_value is not None else None
            except (TypeError, ValueError):
                amount = None
            if expected_amount is not None and amount is not None:
                if not Decimal(str(amount)).quantize(Decimal("0.01")) >= Decimal(str(expected_amount)).quantize(Decimal("0.01")):
                    continue
            return WalletPaymentStatus(
                success=True,
                operation_id=op.get("operation_id") or op.get("operationId"),
                amount=amount,
                currency=op.get("currency") or op.get("amount_currency"),
                raw=op,
            )
        return WalletPaymentStatus(success=False)

    @staticmethod
    def generate_label(purchase_id: int) -> str:
        return f"purchase-{purchase_id}-{uuid4().hex[:8]}"


async def get_yoomoney_wallet_client() -> YooMoneyWalletClient:
    return YooMoneyWalletClient()
