from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..models import PurchaseSession
from ..models.enums import PurchaseStatus


async def cleanup_expired_tokens(session_factory: async_sessionmaker[None]) -> int:
    """Mark expired purchase sessions and remove stale rows."""
    now = datetime.now(timezone.utc)
    removed = 0
    async with session_factory() as session:
        result = await session.execute(
            select(PurchaseSession).where(
                PurchaseSession.expires_at.is_not(None),
                PurchaseSession.expires_at < now,
            )
        )
        for purchase in result.scalars().all():
            purchase.status = PurchaseStatus.EXPIRED.value
            purchase.token = None
        await session.commit()

        deleted = await session.execute(
            delete(PurchaseSession).where(
                PurchaseSession.status == PurchaseStatus.EXPIRED.value,
                PurchaseSession.expires_at.is_not(None),
                PurchaseSession.expires_at < now,
            )
        )
        removed = deleted.rowcount or 0
        await session.commit()
    return removed
