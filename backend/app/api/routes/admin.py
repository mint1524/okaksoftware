from __future__ import annotations

import base64
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...api.deps import get_app_settings, get_db_session
from ...models import PurchaseSession, TokenEvent
from ...models.enums import PurchaseStatus, TokenEventType
from ...services.tokens import TokenManager

router = APIRouter(prefix="/admin", tags=["admin"])


def _validate_secret(settings, header_value: str | None) -> bool:
    if not settings.yoomoney_webhook_secret:
        return True
    if not header_value:
        return False
    expected = settings.yoomoney_webhook_secret.strip()
    if header_value.startswith("Basic "):
        try:
            decoded = base64.b64decode(header_value[6:]).decode("utf-8")
        except Exception:  # pragma: no cover - invalid base64
            return False
        return decoded.split(":", 1)[-1] == expected or decoded == expected
    return header_value == expected


@router.post("/payments/yoomoney/webhook")
async def yoomoney_webhook(
    payload: dict[str, Any],
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    settings=Depends(get_app_settings),
) -> dict[str, Any]:
    if not _validate_secret(settings, request.headers.get("Authorization")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")

    event = payload.get("event")
    obj = payload.get("object") or {}
    payment_id = obj.get("id")
    if not payment_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing payment id")

    stmt = (
        select(PurchaseSession)
        .options(selectinload(PurchaseSession.product))
        .where(PurchaseSession.payment_id == payment_id)
    )
    purchase = await session.scalar(stmt)
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found")

    manager = TokenManager(settings)
    response: dict[str, Any] = {"status": "ok", "purchase_id": purchase.id, "event": event}

    if event == "payment.succeeded":
        purchase.status = PurchaseStatus.PAID.value
        if not purchase.token:
            token = manager.generate_token()
            purchase.token = token
            purchase.expires_at = manager.expires_at()
            domain = manager.domain_for_type(purchase.domain_type or purchase.product.type)
            response["token_url"] = manager.build_link(domain, token)
        session.add(TokenEvent(purchase_id=purchase.id, event_type=TokenEventType.ISSUED.value, payload={"payment_id": payment_id}))
    elif event in {"payment.canceled", "payment.expired"}:
        purchase.status = PurchaseStatus.FAILED.value
        purchase.token = None
        session.add(TokenEvent(purchase_id=purchase.id, event_type=TokenEventType.FAILED.value, payload={"payment_id": payment_id, "event": event}))
    else:
        # ignore other events
        pass

    purchase.extra = (purchase.extra or {}) | {"yoomoney": obj}
    await session.commit()

    if purchase.token and "token_url" not in response:
        domain = manager.domain_for_type(purchase.domain_type or purchase.product.type)
        response["token_url"] = manager.build_link(domain, purchase.token)
        response["expires_at"] = purchase.expires_at

    return response
