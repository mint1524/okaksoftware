from __future__ import annotations

from enum import Enum


class PurchaseStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    DELIVERED = "delivered"
    EXPIRED = "expired"
    FAILED = "failed"
    REFUNDED = "refunded"


class TokenEventType(str, Enum):
    ISSUED = "issued"
    OPENED = "opened"
    COMPLETED = "completed"
    EXPIRED = "expired"
    FAILED = "failed"

