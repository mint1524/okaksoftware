from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...api.deps import get_app_settings, get_db_session
from ...core.config import Settings
from ...models import PurchaseSession, TokenEvent
from ...models.enums import PurchaseStatus, TokenEventType
from ...services.tokens import TokenManager
from ...services.yoomoney_wallet import YooMoneyWalletClient, get_yoomoney_wallet_client

router = APIRouter(prefix="/admin", tags=["admin"])


class YooMoneyCheckRequest(BaseModel):
    purchase_id: int | None = None
    payment_label: str | None = None


@router.post("/payments/yoomoney/check")
async def check_yoomoney_payment(
    payload: YooMoneyCheckRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
    wallet: YooMoneyWalletClient = Depends(get_yoomoney_wallet_client),
) -> dict[str, Any]:
    if not payload.purchase_id and not payload.payment_label:
        raise HTTPException(status_code=400, detail="purchase_id or payment_label is required")

    stmt = select(PurchaseSession).options(selectinload(PurchaseSession.product))
    if payload.purchase_id:
        stmt = stmt.where(PurchaseSession.id == payload.purchase_id)
    elif payload.payment_label:
        stmt = stmt.where(PurchaseSession.payment_label == payload.payment_label)

    purchase = await session.scalar(stmt)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")

    if purchase.payment_provider != "yoomoney_wallet" or not purchase.payment_label:
        return {"status": purchase.status, "message": "Not a YooMoney wallet payment"}

    check = await wallet.check_payment(purchase.payment_label, purchase.payment_amount)
    manager = TokenManager(settings)
    response: dict[str, Any] = {
        "status": purchase.status,
        "payment_label": purchase.payment_label,
        "payment_amount": purchase.payment_amount,
        "payment_currency": purchase.payment_currency,
        "checked": bool(check.success),
    }

    if check.success:
        purchase.status = PurchaseStatus.PAID.value
        if check.amount is not None:
            purchase.payment_amount = check.amount
        if check.currency:
            purchase.payment_currency = check.currency
        if not purchase.token:
            token = manager.generate_token()
            purchase.token = token
            purchase.expires_at = manager.expires_at()
            session.add(
                TokenEvent(
                    purchase_id=purchase.id,
                    event_type=TokenEventType.ISSUED.value,
                    payload={"operation_id": check.operation_id, "source": "admin-check"},
                )
            )
            domain = manager.domain_for_type(purchase.domain_type or (purchase.product.type if purchase.product else ""))
            response["token_url"] = manager.build_link(domain, token)
        response["status"] = purchase.status
        await session.commit()
    else:
        await session.commit()

    return response
