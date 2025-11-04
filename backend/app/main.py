from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.router import api_router
from .core.config import get_settings
from .core.db import lifespan as db_lifespan
from .services.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    async with db_lifespan(None):
        if settings.scheduler_enabled:
            scheduler.start()
        yield
        if settings.scheduler_enabled:
            await scheduler.shutdown()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.project_name, lifespan=lifespan)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    application.include_router(api_router, prefix=settings.api_prefix)

    @application.get("/")
    async def root():
        return {"status": "ok", "name": settings.project_name}

    return application


app = create_app()
