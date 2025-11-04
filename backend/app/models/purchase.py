from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .enums import PurchaseStatus

if TYPE_CHECKING:
    from .product import Product, ProductVariant
    from .user import User


class PurchaseSession(Base, TimestampMixin):
    __tablename__ = "purchase_sessions"
    __table_args__ = (
        Index(
            "ix_purchase_sessions_token_unique",
            "token",
            unique=True,
            postgresql_where=text("token IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default=PurchaseStatus.PENDING.value)
    digiseller_order_id: Mapped[str | None] = mapped_column(String(120), index=True)
    invoice_url: Mapped[str | None] = mapped_column(String(512))
    token: Mapped[str | None] = mapped_column(String(128), unique=True, index=True)
    domain_type: Mapped[str | None] = mapped_column(String(50))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extra: Mapped[dict | None] = mapped_column("metadata", JSONB, default=dict)

    user: Mapped["User"] = relationship(back_populates="purchases")
    product: Mapped["Product"] = relationship(back_populates="purchases")
    variant: Mapped["ProductVariant"] = relationship(back_populates="purchases")
    events: Mapped[list["TokenEvent"]] = relationship(back_populates="purchase", cascade="all, delete-orphan")


class TokenEvent(Base):
    __tablename__ = "token_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchase_sessions.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    purchase: Mapped[PurchaseSession] = relationship(back_populates="events")
