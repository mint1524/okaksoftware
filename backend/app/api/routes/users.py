from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ...api.deps import get_app_settings, get_db_session
from ...core.config import Settings
from ...models import PurchaseSession, TokenEvent, User
from ...models.enums import PurchaseStatus, TokenEventType
from ...schemas.purchase import PurchaseWithProductOut
from ...schemas.user import UserCreate, UserOut
from ...services.tokens import TokenManager
from ...services.yoomoney_wallet import YooMoneyWalletClient, get_yoomoney_wallet_client

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserOut)
async def register_user(payload: UserCreate, session: AsyncSession = Depends(get_db_session)) -> UserOut:
    user = await session.scalar(select(User).where(User.telegram_id == payload.telegram_id))
    if not user:
        user = User(**payload.model_dump())
        session.add(user)
    else:
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(user, field, value)
    await session.commit()
    await session.refresh(user)
    return user


@router.get("/{telegram_id}", response_model=UserOut)
async def get_user(telegram_id: int, session: AsyncSession = Depends(get_db_session)) -> UserOut:
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{telegram_id}/purchases", response_model=list[PurchaseWithProductOut])
async def get_user_purchases(
    telegram_id: int,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
    wallet: YooMoneyWalletClient = Depends(get_yoomoney_wallet_client),
) -> list[PurchaseWithProductOut]:
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stmt = (
        select(PurchaseSession)
        .options(joinedload(PurchaseSession.product), joinedload(PurchaseSession.variant))
        .where(PurchaseSession.user_id == user.id)
        .order_by(PurchaseSession.created_at.desc())
    )
    result = await session.execute(stmt)
    purchases = result.scalars().all()

    manager = TokenManager(settings)
    updated = False
    outputs: list[PurchaseWithProductOut] = []

    for item in purchases:
        token_url = None
        if item.payment_provider == "yoomoney_wallet" and item.status == PurchaseStatus.PENDING.value and item.payment_label:
            try:
                check = await wallet.check_payment(item.payment_label, item.payment_amount)
            except Exception:  # pragma: no cover - network failure path
                check = None
            if check and check.success:
                item.status = PurchaseStatus.PAID.value
                if check.amount is not None:
                    item.payment_amount = check.amount
                if check.currency:
                    item.payment_currency = check.currency
                if not item.token:
                    item.token = manager.generate_token()
                    item.expires_at = manager.expires_at()
                    session.add(
                        TokenEvent(
                            purchase_id=item.id,
                            event_type=TokenEventType.ISSUED.value,
                            payload={"operation_id": check.operation_id},
                        )
                    )
                updated = True
        if item.token:
            domain = manager.domain_for_type(item.domain_type or (item.product.type if item.product else ""))
            token_url = manager.build_link(domain, item.token)

        outputs.append(
            PurchaseWithProductOut(
                id=item.id,
                status=item.status,
                payment_provider=item.payment_provider,
                payment_label=item.payment_label,
                payment_amount=item.payment_amount,
                payment_currency=item.payment_currency,
                invoice_url=item.invoice_url,
                token=item.token,
                domain_type=item.domain_type,
                expires_at=item.expires_at,
                delivered_at=item.delivered_at,
                metadata=item.extra,
                created_at=item.created_at,
                updated_at=item.updated_at,
                product_title=item.product.title if item.product else "",
                product_type=item.product.type if item.product else "",
                variant_name=item.variant.name if item.variant else "",
                token_url=token_url,
            )
        )

    if updated:
        await session.commit()

    return outputs
