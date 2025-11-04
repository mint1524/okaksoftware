from __future__ import annotations

from pydantic import BaseModel

from .common import ORMModel


class UserCreate(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None


class UserOut(ORMModel):
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    language_code: str | None

