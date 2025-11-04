from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .product import ProductOut
from .purchase import PurchaseWithProductOut


class AdminLoginRequest(BaseModel):
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AdminSummary(BaseModel):
    users_total: int
    products_total: int
    active_products: int
    purchases_total: int
    purchases_pending: int
    purchases_paid: int
    purchases_delivered: int
    tokens_active: int


class ProductCreate(BaseModel):
    title: str
    slug: str
    type: str
    description: str | None = None
    support_contact: str | None = None
    domain_hint: str | None = None
    is_active: bool = True
    metadata: dict[str, Any] | None = None


class ProductUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    type: str | None = None
    description: str | None = None
    support_contact: str | None = None
    domain_hint: str | None = None
    is_active: bool | None = None
    metadata: dict[str, Any] | None = None


class VariantCreate(BaseModel):
    name: str
    price: float
    currency: str = "RUB"
    digiseller_product_id: str | None = None
    payment_url: str | None = None
    sort_order: int = 0
    metadata: dict[str, Any] | None = None


class VariantUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    currency: str | None = None
    digiseller_product_id: str | None = None
    payment_url: str | None = None
    sort_order: int | None = None
    metadata: dict[str, Any] | None = None


class FileAssetCreate(BaseModel):
    product_type: str
    label: str
    path: str
    os_type: str | None = None
    checksum: str | None = None


class FileAssetUpdate(BaseModel):
    label: str | None = None
    path: str | None = None
    os_type: str | None = None
    checksum: str | None = None


class FileAssetOut(BaseModel):
    id: int
    product_type: str
    label: str
    path: str
    os_type: str | None
    checksum: str | None
    created_at: datetime
    updated_at: datetime


class PurchaseListFilters(BaseModel):
    status: str | None = None
    product_type: str | None = None


class PurchaseListResponse(BaseModel):
    items: list[PurchaseWithProductOut]


class ProductListResponse(BaseModel):
    items: list[ProductOut]
