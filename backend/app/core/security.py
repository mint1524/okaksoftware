from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    expire_delta = timedelta(minutes=expires_minutes or settings.admin_token_expire_minutes)
    expire = datetime.now(timezone.utc) + expire_delta
    payload: Dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.admin_jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any] | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.admin_jwt_secret, algorithms=["HS256"])
    except JWTError:
        return None
    return payload
