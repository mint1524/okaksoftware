from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common import ORMModel


class ProductVariantOut(ORMModel):
    id: int
    name: str
    price: float
    currency: str
    external_id: str | None
    payment_url: str | None
    sort_order: int
    metadata: dict[str, Any] | None = Field(alias="extra")
    created_at: datetime
    updated_at: datetime


class ProductOut(ORMModel):
    id: int
    title: str
    slug: str
    type: str
    description: str | None
    support_contact: str | None
    domain_hint: str | None
    is_active: bool
    metadata: dict[str, Any] | None = Field(alias="extra")
    variants: list[ProductVariantOut]
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    items: list[ProductOut]
