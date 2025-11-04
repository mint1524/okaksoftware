from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..core.config import Settings, get_settings
from ..core.security import decode_access_token, verify_password


http_bearer = HTTPBearer(auto_error=False)
from ..core.db import get_session


async def get_db_session(session=Depends(get_session)):
    return session


def get_app_settings() -> Settings:
    return get_settings()


def validate_admin_password(password: str) -> bool:
    settings = get_settings()
    if not settings.admin_password_hash:
        return False
    return verify_password(password, settings.admin_password_hash)


def get_admin_token(credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer)) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")
    payload = decode_access_token(credentials.credentials)
    if not payload or payload.get("sub") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload
