from __future__ import annotations

from pydantic import BaseModel

from .common import ORMModel


class FileAssetCreate(BaseModel):
    product_type: str
    label: str
    path: str
    os_type: str | None = None
    checksum: str | None = None


class FileAssetOut(ORMModel):
    id: int
    product_type: str
    label: str
    path: str
    os_type: str | None
    checksum: str | None

