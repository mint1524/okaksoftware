from __future__ import annotations

from fastapi import Depends

from ..core.config import Settings, get_settings
from ..core.db import get_session


async def get_db_session(session=Depends(get_session)):
    return session


def get_app_settings() -> Settings:
    return get_settings()
