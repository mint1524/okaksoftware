from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import get_settings


settings = get_settings()
engine = create_async_engine(settings.database_url.unicode_string(), echo=settings.database_echo)
AsyncSessionMaker = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def lifespan(engine_override=None) -> AsyncIterator[None]:
    try:
        yield
    finally:
        await (engine_override or engine).dispose()


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionMaker() as session:
        yield session

