from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...api.deps import get_app_settings, get_db_session
from ...core.config import Settings
from ...models import ProductVariant, PurchaseSession, TokenEvent, User
from ...models.enums import PurchaseStatus, TokenEventType
from ...schemas.purchase import PurchaseCreate, PurchaseCreateResponse
from ...services.tokens import TokenManager
from ...services.yoomoney_wallet import YooMoneyWalletClient, get_yoomoney_wallet_client

router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.post("/", response_model=PurchaseCreateResponse)
async def create_purchase(
    payload: PurchaseCreate,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
    wallet: YooMoneyWalletClient = Depends(get_yoomoney_wallet_client),
) -> PurchaseCreateResponse:
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
        payment_provider="yoomoney_wallet",
        payment_amount=float(variant.price),
        payment_currency=variant.currency,
    )
    session.add(purchase)
    await session.flush()

    payment_url = variant.payment_url
    if not payment_url:
        if not settings.yoomoney_wallet_account:
            raise HTTPException(status_code=503, detail="YooMoney wallet not configured")
        label = YooMoneyWalletClient.generate_label(purchase.id)
        purchase.payment_label = label
        description = f"{variant.product.title} – {variant.name}"
        success_url = settings.yoomoney_quickpay_success_url
        payment_url = wallet.build_payment_link(
            amount=float(variant.price),
            label=label,
            description=description,
            success_url=str(success_url) if success_url else None,
        )
        purchase.invoice_url = payment_url
    else:
        purchase.payment_provider = "manual"
        purchase.payment_label = None
        purchase.payment_amount = None
        purchase.payment_currency = None
        purchase.invoice_url = payment_url

    await session.commit()
    await session.refresh(purchase)

    manager = TokenManager(settings)
    # ensure token events exist if manual payment considered immediate (no wallet)
    if purchase.payment_provider == "manual" and payment_url:
        session.add(
            TokenEvent(
                purchase_id=purchase.id,
                event_type=TokenEventType.OPENED.value,
                payload={"payment_url": payment_url},
            )
        )
        await session.commit()

    return PurchaseCreateResponse(purchase=purchase, payment_url=payment_url)
