from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common import ORMModel


class PurchaseCreate(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None
    product_variant_id: int


class PurchaseSessionOut(ORMModel):
    id: int
    status: str
    payment_provider: str
    payment_label: str | None
    payment_amount: float | None
    payment_currency: str | None
    invoice_url: str | None
    token: str | None
    domain_type: str | None
    expires_at: datetime | None
    delivered_at: datetime | None
    metadata: dict[str, Any] | None = Field(alias="extra")
    created_at: datetime
    updated_at: datetime


class PurchaseCreateResponse(BaseModel):
    purchase: PurchaseSessionOut
    payment_url: str | None


class PurchaseWithProductOut(PurchaseSessionOut):
    product_title: str
    product_type: str
    variant_name: str
    token_url: str | None = None
