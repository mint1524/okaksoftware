from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ...api.deps import get_admin_token, get_app_settings, get_db_session, validate_admin_password
from ...core.config import Settings
from ...core.security import create_access_token
from ...models import FileAsset, Product, ProductVariant, PurchaseSession, User
from ...models.enums import PurchaseStatus
from ...schemas.admin import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminSummary,
    FileAssetCreate,
    FileAssetOut,
    FileAssetUpdate,
    ProductCreate,
    ProductListResponse,
    ProductUpdate,
    PurchaseListFilters,
    PurchaseListResponse,
    VariantCreate,
    VariantUpdate,
)

router = APIRouter(prefix="/admin/panel", tags=["admin-panel"])


async def _fetch_products(session: AsyncSession) -> list[Product]:
    stmt = select(Product).options(selectinload(Product.variants)).order_by(Product.created_at.desc())
    result = await session.execute(stmt)
    return result.scalars().unique().all()


@router.post("/auth/login", response_model=AdminLoginResponse)
async def admin_login(payload: AdminLoginRequest, settings: Settings = Depends(get_app_settings)) -> AdminLoginResponse:
    if not settings.admin_password_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin access is not configured")
    if not validate_admin_password(payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    access_token = create_access_token("admin")
    return AdminLoginResponse(access_token=access_token, expires_in=settings.admin_token_expire_minutes * 60)


@router.get("/dashboard/summary", response_model=AdminSummary)
async def admin_summary(
    session: AsyncSession = Depends(get_db_session),
    _: dict = Depends(get_admin_token),
) -> AdminSummary:
    users_total = await session.scalar(select(func.count(User.id))) or 0
    products_total = await session.scalar(select(func.count(Product.id))) or 0
    active_products = await session.scalar(select(func.count(Product.id)).where(Product.is_active.is_(True))) or 0
    purchases_total = await session.scalar(select(func.count(PurchaseSession.id))) or 0
    purchases_pending = await session.scalar(
        select(func.count(PurchaseSession.id)).where(PurchaseSession.status == PurchaseStatus.PENDING.value)
    ) or 0
    purchases_paid = await session.scalar(
        select(func.count(PurchaseSession.id)).where(PurchaseSession.status == PurchaseStatus.PAID.value)
    ) or 0
    purchases_delivered = await session.scalar(
        select(func.count(PurchaseSession.id)).where(PurchaseSession.status == PurchaseStatus.DELIVERED.value)
    ) or 0
    tokens_active = await session.scalar(
        select(func.count(PurchaseSession.id)).where(
            PurchaseSession.token.is_not(None),
            PurchaseSession.status.in_([PurchaseStatus.PAID.value, PurchaseStatus.DELIVERED.value]),
        )
    ) or 0

    return AdminSummary(
        users_total=users_total,
        products_total=products_total,
        active_products=active_products,
        purchases_total=purchases_total,
        purchases_pending=purchases_pending,
        purchases_paid=purchases_paid,
        purchases_delivered=purchases_delivered,
        tokens_active=tokens_active,
    )


@router.get("/products", response_model=ProductListResponse)
async def admin_products(
    session: AsyncSession = Depends(get_db_session),
    _: dict = Depends(get_admin_token),
) -> ProductListResponse:
    products = await _fetch_products(session)
    return ProductListResponse(items=products)


@router.post("/products", response_model=ProductListResponse)
async def admin_create_product(
    payload: ProductCreate,
    session: AsyncSession = Depends(get_db_session),
    _: dict = Depends(get_admin_token),
) -> ProductListResponse:
    product = Product(
        title=payload.title,
        slug=payload.slug,
        type=payload.type,
        description=payload.description,
        support_contact=payload.support_contact,
        domain_hint=payload.domain_hint,
        is_active=payload.is_active,
        extra=payload.metadata or {},
    )
    session.add(product)
    await session.flush()
    await session.commit()
    products = await _fetch_products(session)
    return ProductListResponse(items=products)


@router.put("/products/{product_id}", response_model=ProductListResponse)
async def admin_update_product(
    product_id: int,
    payload: ProductUpdate,
    session: AsyncSession = Depends(get_db_session),
    _: dict = Depends(get_admin_token),
) -> ProductListResponse:
    product = await session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "metadata":
            product.extra = value or {}
        else:
            setattr(product, field, value)
    await session.commit()
    products = await _fetch_products(session)
    return ProductListResponse(items=products)


@router.delete("/products/{product_id}", response_model=ProductListResponse)
async def admin_delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: dict = Depends(get_admin_token),
) -> ProductListResponse:
    product = await session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    await session.delete(product)
    await session.commit()
    products = await _fetch_products(session)
    return ProductListResponse(items=products)


@router.post("/products/{product_id}/variants", response_model=ProductListResponse)
async def admin_create_variant(
    product_id: int,
    payload: VariantCreate,
    session: AsyncSession = Depends(get_db_session),
    _: dict = Depends(get_admin_token),
) -> ProductListResponse:
    product = await session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        variant = ProductVariant(
            product_id=product_id,
            name=payload.name,
            price=payload.price,
            currency=payload.currency,
            external_id=payload.external_id,
            payment_url=payload.payment_url,
            sort_order=payload.sort_order,
            extra=payload.metadata or {},
        )
    session.add(variant)
    await session.flush()
    await session.commit()
    products = await _fetch_products(session)
    return ProductListResponse(items=products)


@router.put("/variants/{variant_id}", response_model=ProductListResponse)
async def admin_update_variant(
    variant_id: int,
    payload: VariantUpdate,
    session: AsyncSession = Depends(get_db_session),
    _: dict = Depends(get_admin_token),
) -> ProductListResponse:
    variant = await session.get(ProductVariant, variant_id)
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "metadata":
            variant.extra = value or {}
        else:
            setattr(variant, field, value)
    await session.commit()
    products = await _fetch_products(session)
    return ProductListResponse(items=products)


@router.delete("/variants/{variant_id}", response_model=ProductListResponse)
async def admin_delete_variant(
    variant_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: dict = Depends(get_admin_token),
) -> ProductListResponse:
    variant = await session.get(ProductVariant, variant_id)
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
    await session.delete(variant)
    await session.commit()
    products = await _fetch_products(session)
    return ProductListResponse(items=products)


@router.get("/purchases", response_model=PurchaseListResponse)
async def admin_purchases(
    status_filter: str | None = Query(default=None, alias="status"),
    product_type: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    _: dict = Depends(get_admin_token),
) -> PurchaseListResponse:
    filters = []
    if status_filter:
        filters.append(PurchaseSession.status == status_filter)
    if product_type:
        filters.append(PurchaseSession.product.has(Product.type == product_type))

    stmt = (
        select(PurchaseSession)
        .options(joinedload(PurchaseSession.product), joinedload(PurchaseSession.variant))
        .where(*filters)  # no effect if empty
        .order_by(PurchaseSession.created_at.desc())
        .limit(200)
    )
    result = await session.execute(stmt)
    purchases = result.scalars().all()
    return PurchaseListResponse(items=purchases)


@router.get("/files", response_model=list[FileAssetOut])
async def admin_list_files(
    session: AsyncSession = Depends(get_db_session),
    _: dict = Depends(get_admin_token),
) -> list[FileAssetOut]:
    result = await session.execute(select(FileAsset).order_by(FileAsset.created_at.desc()))
    return list(result.scalars().all())


@router.post("/files", response_model=list[FileAssetOut])
async def admin_create_file(
    payload: FileAssetCreate,
    session: AsyncSession = Depends(get_db_session),
    _: dict = Depends(get_admin_token),
) -> list[FileAssetOut]:
    asset = FileAsset(**payload.model_dump())
    session.add(asset)
    await session.flush()
    await session.commit()
    return await admin_list_files(session)


@router.put("/files/{file_id}", response_model=list[FileAssetOut])
async def admin_update_file(
    file_id: int,
    payload: FileAssetUpdate,
    session: AsyncSession = Depends(get_db_session),
    _: dict = Depends(get_admin_token),
) -> list[FileAssetOut]:
    asset = await session.get(FileAsset, file_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File asset not found")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)
    await session.commit()
    return await admin_list_files(session)


@router.delete("/files/{file_id}", response_model=list[FileAssetOut])
async def admin_delete_file(
    file_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: dict = Depends(get_admin_token),
) -> list[FileAssetOut]:
    asset = await session.get(FileAsset, file_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File asset not found")
    await session.delete(asset)
    await session.commit()
    return await admin_list_files(session)
