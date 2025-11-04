from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...api.deps import get_app_settings, get_db_session
from ...models import FileAsset, PurchaseSession, TokenEvent
from ...models.enums import PurchaseStatus, TokenEventType
from ...schemas.token import TokenActionResult, TokenDetailsOut, TokenSubmitPayload
from ...services.tokens import TokenManager

router = APIRouter(prefix="/tokens", tags=["tokens"])


async def _get_purchase_or_404(token: str, session: AsyncSession) -> PurchaseSession:
    stmt = (
        select(PurchaseSession)
        .options(
            selectinload(PurchaseSession.product),
            selectinload(PurchaseSession.variant),
        )
        .where(PurchaseSession.token == token)
    )
    purchase = await session.scalar(stmt)
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
    return purchase


async def _ensure_active(purchase: PurchaseSession, session: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    if purchase.expires_at and purchase.expires_at < now:
        purchase.status = PurchaseStatus.EXPIRED.value
        purchase.token = None
        await session.commit()
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Token expired")
    if purchase.status not in {PurchaseStatus.PAID.value, PurchaseStatus.DELIVERED.value}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Token unavailable in status {purchase.status}")


async def _append_event(session: AsyncSession, purchase: PurchaseSession, event_type: TokenEventType, payload: dict | None = None) -> None:
    event = TokenEvent(purchase_id=purchase.id, event_type=event_type.value, payload=payload or {})
    session.add(event)
    await session.flush()


@router.get("/{token}", response_model=TokenDetailsOut)
async def fetch_token_details(token: str, session: AsyncSession = Depends(get_db_session), settings=Depends(get_app_settings)) -> TokenDetailsOut:
    purchase = await _get_purchase_or_404(token, session)
    await _ensure_active(purchase, session)

    manager = TokenManager(settings)
    domain = manager.domain_for_type(purchase.domain_type or purchase.product.type)

    metadata = dict(purchase.extra or {})
    if purchase.product.type == "vpn":
        assets = await session.execute(select(FileAsset).where(FileAsset.product_type == "vpn"))
        downloads = [
            {
                "label": asset.label,
                "url": f"https://{domain}/static/vpn/{asset.path}",
            }
            for asset in assets.scalars().all()
        ]
        if downloads:
            metadata.setdefault("downloads", downloads)
    if purchase.product.extra:
        metadata.setdefault("product", purchase.product.extra)

    await _append_event(session, purchase, TokenEventType.OPENED)
    await session.commit()

    return TokenDetailsOut(
        token=token,
        status=purchase.status,
        expires_at=purchase.expires_at,
        delivered_at=purchase.delivered_at,
        product_type=purchase.product.type,
        product_title=purchase.product.title,
        support_contact=purchase.product.support_contact or settings.support_username,
        domain=domain,
        metadata=metadata,
    )


@router.post("/{token}/submit", response_model=TokenActionResult)
async def submit_token_payload(
    token: str,
    payload: TokenSubmitPayload,
    session: AsyncSession = Depends(get_db_session),
) -> TokenActionResult:
    purchase = await _get_purchase_or_404(token, session)
    await _ensure_active(purchase, session)

    metadata = purchase.extra or {}
    metadata["submitted_payload"] = payload.data
    purchase.extra = metadata
    await _append_event(session, purchase, TokenEventType.OPENED, payload={"submitted": payload.data})
    await session.commit()

    return TokenActionResult(status="accepted", message="Payload received")


@router.post("/{token}/complete", response_model=TokenActionResult)
async def complete_token(token: str, session: AsyncSession = Depends(get_db_session)) -> TokenActionResult:
    purchase = await _get_purchase_or_404(token, session)
    await _ensure_active(purchase, session)

    now = datetime.now(timezone.utc)
    purchase.status = PurchaseStatus.DELIVERED.value
    purchase.delivered_at = now
    purchase.token = None
    await _append_event(session, purchase, TokenEventType.COMPLETED)
    await session.commit()

    return TokenActionResult(status="success", message="Delivery marked as complete")


@router.post("/{token}/fail", response_model=TokenActionResult)
async def fail_token(token: str, session: AsyncSession = Depends(get_db_session)) -> TokenActionResult:
    purchase = await _get_purchase_or_404(token, session)
    await _ensure_active(purchase, session)

    purchase.status = PurchaseStatus.FAILED.value
    await _append_event(session, purchase, TokenEventType.FAILED)
    await session.commit()

    return TokenActionResult(status="failed", message="Token marked as failed")


@router.post("/{token}/confirm", response_model=TokenActionResult)
async def confirm_delivery(token: str, session: AsyncSession = Depends(get_db_session)) -> TokenActionResult:
    purchase = await _get_purchase_or_404(token, session)
    await _ensure_active(purchase, session)

    now = datetime.now(timezone.utc)
    purchase.status = PurchaseStatus.DELIVERED.value
    purchase.delivered_at = now
    purchase.token = None
    await _append_event(session, purchase, TokenEventType.COMPLETED, payload={"source": "user_confirm"})
    await session.commit()

    return TokenActionResult(status="success", message="Token confirmed by user")
