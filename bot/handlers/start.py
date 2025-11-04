from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from ..config import settings
from ..keyboards.menu import (
    MenuCallback,
    ProductCallback,
    VariantCallback,
    PurchaseCallback,
    main_menu_kb,
    product_list_kb,
    purchases_kb,
    support_button,
    variants_kb,
)
from ..services.backend import BackendClient

router = Router()


def _backend_client() -> BackendClient:
    return BackendClient()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    client = _backend_client()
    try:
        user = message.from_user
        if user:
            await client.register_user(
                {
                    "telegram_id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "language_code": user.language_code,
                }
            )
        await message.answer(
            "Добро пожаловать! Выберите действие:",
            reply_markup=main_menu_kb().as_markup(),
        )
    finally:
        await client.close()


@router.callback_query(MenuCallback.filter())
async def handle_menu_callback(query: CallbackQuery, callback_data: MenuCallback) -> None:
    client = _backend_client()
    try:
        action = callback_data.action
        user = query.from_user
        if action == "back_main":
            await query.message.edit_text(
                "Главное меню",
                reply_markup=main_menu_kb().as_markup(),
            )
        elif action == "catalog":
            products = await client.list_products()
            await query.message.edit_text(
                "Выберите товар:",
                reply_markup=product_list_kb(products).as_markup(),
            )
        elif action == "orders" and user:
            purchases = await client.get_user_purchases(user.id)
            if purchases:
                await query.message.edit_text(
                    "Ваши покупки:",
                    reply_markup=purchases_kb(purchases).as_markup(),
                )
            else:
                await query.message.edit_text(
                    "У вас пока нет покупок.",
                    reply_markup=main_menu_kb().as_markup(),
                )
        elif action == "profile" and user:
            profile = await client.get_user(user.id)
            if not profile:
                text = "Профиль не найден. Отправьте /start для регистрации."
            else:
                text = (
                    "Профиль:\n"
                    f"ID: {profile.get('telegram_id')}\n"
                    f"Username: @{profile.get('username') or '—'}\n"
                )
            await query.message.edit_text(text, reply_markup=main_menu_kb().as_markup())
        elif action == "support":
            kb = support_button(settings.support_username)
            await query.message.answer(
                "Связь с поддержкой:",
                reply_markup=kb,
            )
            await query.answer()
            return
        else:
            await query.message.edit_reply_markup(reply_markup=main_menu_kb().as_markup())
        await query.answer()
    finally:
        await client.close()


@router.callback_query(ProductCallback.filter())
async def handle_product(query: CallbackQuery, callback_data: ProductCallback) -> None:
    client = _backend_client()
    try:
        products = await client.list_products()
        product = next((p for p in products if p.get("id") == callback_data.product_id), None)
        if not product:
            await query.answer("Товар не найден", show_alert=True)
            return
        variants = product.get("variants", [])
        description = product.get("description") or "Описание отсутствует"
        await query.message.edit_text(
            f"{product.get('title')}\n\n{description}",
            reply_markup=variants_kb(product.get("id"), variants).as_markup(),
        )
        await query.answer()
    finally:
        await client.close()


@router.callback_query(VariantCallback.filter())
async def handle_variant(query: CallbackQuery, callback_data: VariantCallback) -> None:
    user = query.from_user
    if not user:
        await query.answer("Пользователь не определен", show_alert=True)
        return

    client = _backend_client()
    try:
        payload = {
            "telegram_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language_code": user.language_code,
            "product_variant_id": callback_data.variant_id,
        }
        response = await client.create_purchase(payload)
        payment_url = response.get("payment_url")
        await query.answer("Ссылка сформирована")
        if payment_url:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

            kb = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Перейти к оплате", url=payment_url)]]
            )
            await query.message.answer("Оплатите заказ по ссылке ниже", reply_markup=kb)
        else:
            await query.message.answer("Ссылка на оплату будет отправлена позже")
        await query.message.answer(
            "Возвращаемся в меню",
            reply_markup=main_menu_kb().as_markup(),
        )
    finally:
        await client.close()


@router.callback_query(PurchaseCallback.filter())
async def handle_purchase_info(query: CallbackQuery, callback_data: PurchaseCallback) -> None:
    if not query.from_user or callback_data.purchase_id is None:
        await query.answer()
        return

    client = _backend_client()
    try:
        purchases = await client.get_user_purchases(query.from_user.id)
        purchase = next((item for item in purchases if item.get("id") == callback_data.purchase_id), None)
        if not purchase:
            await query.answer("Покупка не найдена", show_alert=True)
            return
        text_lines = [f"Товар: {purchase.get('product_title')}"]
        text_lines.append(f"Тариф: {purchase.get('variant_name')}")
        text_lines.append(f"Статус: {purchase.get('status')}")
        if purchase.get("expires_at"):
            text_lines.append(f"Действительно до: {purchase.get('expires_at')}")
        if purchase.get("token_url"):
            text_lines.append(f"Ссылка: {purchase.get('token_url')}")
        await query.message.edit_text(
            "\n".join(text_lines),
            reply_markup=purchases_kb(purchases).as_markup(),
        )
        await query.answer()
    finally:
        await client.close()
