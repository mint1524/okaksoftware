from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...api.deps import get_db_session
from ...models import ProductVariant, PurchaseSession, User
from ...models.enums import PurchaseStatus
from ...schemas.purchase import PurchaseCreate, PurchaseCreateResponse
from ...services.digiseller import DigisellerClient, get_digiseller_client

router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.post("/", response_model=PurchaseCreateResponse)
async def create_purchase(
    payload: PurchaseCreate,
    session: AsyncSession = Depends(get_db_session),
    digiseller: DigisellerClient = Depends(get_digiseller_client),
) -> PurchaseCreateResponse:
    try:
        user = await session.scalar(select(User).where(User.telegram_id == payload.telegram_id))
        if not user:
            user = User(
                telegram_id=payload.telegram_id,
                username=payload.username,
                first_name=payload.first_name,
                last_name=payload.last_name,
                language_code=payload.language_code,
            )
            session.add(user)
            await session.flush()
        else:
            user.username = payload.username or user.username
            user.first_name = payload.first_name or user.first_name
            user.last_name = payload.last_name or user.last_name
            user.language_code = payload.language_code or user.language_code

        stmt = (
            select(ProductVariant)
            .options(selectinload(ProductVariant.product))
            .where(ProductVariant.id == payload.product_variant_id)
        )
        variant = await session.scalar(stmt)
        if not variant or not variant.product or not variant.product.is_active:
            raise HTTPException(status_code=404, detail="Product variant not found")

        purchase = PurchaseSession(
            user_id=user.id,
            product_id=variant.product_id,
            variant_id=variant.id,
            status=PurchaseStatus.PENDING.value,
            domain_type=variant.product.type,
        )
        session.add(purchase)
        await session.flush()

        payment_url = variant.payment_url
        if not payment_url and variant.digiseller_product_id:
            try:
                invoice = await digiseller.create_invoice(variant.digiseller_product_id)
                purchase.digiseller_order_id = invoice.order_id
                purchase.invoice_url = invoice.invoice_url
                payment_url = invoice.invoice_url
            except Exception as exc:  # pragma: no cover - network failure path
                raise HTTPException(
                    status_code=503,
                    detail="Unable to create Digiseller invoice",
                ) from exc
        else:
            purchase.invoice_url = payment_url
            purchase.digiseller_order_id = variant.digiseller_product_id

        await session.commit()
        await session.refresh(purchase)
        return PurchaseCreateResponse(purchase=purchase, payment_url=payment_url)
    finally:
        await digiseller.close()
