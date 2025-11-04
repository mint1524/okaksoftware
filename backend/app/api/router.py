from fastapi import APIRouter

from .routes import admin, admin_panel, health, products, purchases, tokens, users

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(products.router)
api_router.include_router(purchases.router)
api_router.include_router(tokens.router)
api_router.include_router(admin.router)
api_router.include_router(users.router)
api_router.include_router(admin_panel.router)
