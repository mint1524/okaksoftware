from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...api.deps import get_app_settings, get_db_session
from ...models import ProductVariant, PurchaseSession, User
from ...models.enums import PurchaseStatus
from ...schemas.purchase import PurchaseCreate, PurchaseCreateResponse
from ...services.yoomoney import YooMoneyClient, get_yoomoney_client

router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.post("/", response_model=PurchaseCreateResponse)
async def create_purchase(
    payload: PurchaseCreate,
    session: AsyncSession = Depends(get_db_session),
    settings=Depends(get_app_settings),
    yoomoney: YooMoneyClient = Depends(get_yoomoney_client),
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
            payment_provider="yoomoney",
        )
        session.add(purchase)
        await session.flush()

        payment_url = variant.payment_url
        if not payment_url:
            amount = float(variant.price)
            description = f"{variant.product.title} - {variant.name}"
            metadata = {
                "purchase_id": purchase.id,
                "user_id": user.id,
            }
            return_url = settings.yoomoney_return_url
            if not return_url and settings.domain_gpt:
                return_url = f"https://{settings.domain_gpt}/payment/success"
            try:
                payment = await yoomoney.create_payment(
                    amount=amount,
                    currency=variant.currency or "RUB",
                    description=description,
                    metadata=metadata,
                    return_url=return_url,
                )
            except Exception as exc:  # pragma: no cover - network failure path
                raise HTTPException(
                    status_code=503,
                    detail="Unable to create YooMoney payment",
                ) from exc
            purchase.payment_id = payment.payment_id
            purchase.invoice_url = payment.confirmation_url
            payment_url = payment.confirmation_url
        else:
            purchase.payment_provider = "manual"
            purchase.payment_id = None
            purchase.invoice_url = payment_url

        await session.commit()
        await session.refresh(purchase)
        return PurchaseCreateResponse(purchase=purchase, payment_url=payment_url)
    finally:
        await yoomoney.close()
