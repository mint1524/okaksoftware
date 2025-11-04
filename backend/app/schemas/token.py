from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from .common import ORMModel


class TokenDetailsOut(BaseModel):
    token: str
    status: str
    expires_at: datetime
    delivered_at: datetime | None
    product_type: str
    product_title: str
    support_contact: str | None
    domain: str
    metadata: dict[str, Any] | None


class TokenSubmitPayload(BaseModel):
    data: dict[str, Any]


class TokenActionResult(BaseModel):
    status: str
    message: str | None = None


class TokenEventOut(ORMModel):
    id: int
    event_type: str
    payload: dict[str, Any] | None

