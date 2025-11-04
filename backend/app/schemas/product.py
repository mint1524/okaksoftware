from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .common import ORMModel


class ProductVariantOut(ORMModel):
    id: int
    name: str
    price: float
    currency: str
    digiseller_product_id: str | None
    payment_url: str | None
    sort_order: int
    metadata: dict[str, Any] | None = Field(alias="extra")


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


class ProductListResponse(BaseModel):
    items: list[ProductOut]
