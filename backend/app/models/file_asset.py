from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class FileAsset(Base, TimestampMixin):
    __tablename__ = "file_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    os_type: Mapped[str | None] = mapped_column(String(50))
    checksum: Mapped[str | None] = mapped_column(String(128))

