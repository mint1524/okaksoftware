from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ...api.deps import get_db_session
from ...models import Product
from ...schemas.product import ProductListResponse, ProductOut

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=ProductListResponse)
async def list_products(
    session=Depends(get_db_session),
    product_type: str | None = Query(default=None, alias="type"),
) -> ProductListResponse:
    stmt = select(Product).options(selectinload(Product.variants)).where(Product.is_active.is_(True))
    if product_type:
        stmt = stmt.where(Product.type == product_type)

    result = await session.execute(stmt.order_by(Product.type, Product.id))
    products = result.scalars().unique().all()
    return ProductListResponse(items=products)


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, session=Depends(get_db_session)) -> ProductOut:
    stmt = (
        select(Product)
        .options(selectinload(Product.variants))
        .where(Product.id == product_id, Product.is_active.is_(True))
    )
    result = await session.execute(stmt)
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
