from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...api.deps import get_app_settings, get_db_session
from ...models import PurchaseSession, TokenEvent
from ...models.enums import PurchaseStatus, TokenEventType
from ...services.digiseller import DigisellerClient
from ...services.tokens import TokenManager

router = APIRouter(prefix="/admin", tags=["admin"])


class DigisellerWebhookPayload(BaseModel):
    order_id: str
    status: str
    details: dict[str, Any] | None = None


async def _append_event(session: AsyncSession, purchase: PurchaseSession, event_type: TokenEventType, payload: dict | None = None) -> None:
    event = TokenEvent(purchase_id=purchase.id, event_type=event_type.value, payload=payload or {})
    session.add(event)
    await session.flush()


@router.post("/digiseller/webhook")
async def digiseller_webhook(
    payload: DigisellerWebhookPayload,
    session: AsyncSession = Depends(get_db_session),
    settings=Depends(get_app_settings),
    signature: str | None = Header(default=None, alias="X-Digiseller-Signature"),
) -> dict[str, Any]:
    if settings.digiseller_secret and not signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing webhook signature")

    if settings.digiseller_secret:
        if not DigisellerClient.verify_signature(settings.digiseller_secret, signature or "", payload.model_dump()):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    stmt = (
        select(PurchaseSession)
        .options(selectinload(PurchaseSession.product))
        .where(PurchaseSession.digiseller_order_id == payload.order_id)
    )
    purchase = await session.scalar(stmt)
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase session not found")

    manager = TokenManager(settings)
    status_lower = payload.status.lower()

    if status_lower in {"paid", "pay", "completed", "complete"}:
        purchase.status = PurchaseStatus.PAID.value
        if not purchase.token:
            token = manager.generate_token()
            purchase.token = token
            purchase.expires_at = manager.expires_at()
            await _append_event(session, purchase, TokenEventType.ISSUED, payload={"order_id": payload.order_id})
    elif status_lower in {"refunded", "cancelled", "canceled"}:
        purchase.status = PurchaseStatus.REFUNDED.value
        purchase.token = None
        await _append_event(session, purchase, TokenEventType.FAILED, payload={"status": status_lower})
    else:
        await _append_event(session, purchase, TokenEventType.OPENED, payload={"status": status_lower})

    purchase.extra = (purchase.extra or {}) | {"digiseller": payload.details or {}}
    await session.commit()

    response = {"status": "ok", "purchase_id": purchase.id, "current_status": purchase.status}

    if purchase.token:
        domain = manager.domain_for_type(purchase.domain_type or purchase.product.type)
        response["token_url"] = manager.build_link(domain, purchase.token)
        response["expires_at"] = purchase.expires_at

    return response
