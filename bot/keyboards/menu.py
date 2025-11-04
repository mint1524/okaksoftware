from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class MenuCallback(CallbackData, prefix="menu"):
    action: str


class ProductCallback(CallbackData, prefix="product"):
    product_id: int


class VariantCallback(CallbackData, prefix="variant"):
    product_id: int
    variant_id: int


class PurchaseCallback(CallbackData, prefix="purchase"):
    action: str
    purchase_id: int | None = None


def main_menu_kb() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="Каталог", callback_data=MenuCallback(action="catalog"))
    builder.button(text="Мои покупки", callback_data=MenuCallback(action="orders"))
    builder.button(text="Профиль", callback_data=MenuCallback(action="profile"))
    builder.button(text="Поддержка", callback_data=MenuCallback(action="support"))
    builder.adjust(1)
    return builder


def product_list_kb(products: list[dict]) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(text=product.get("title"), callback_data=ProductCallback(product_id=product.get("id")))
    builder.button(text="⬅️ Назад", callback_data=MenuCallback(action="back_main"))
    builder.adjust(1)
    return builder


def variants_kb(product_id: int, variants: list[dict]) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for variant in variants:
        label = f"{variant.get('name')} — {variant.get('price')} {variant.get('currency')}"
        builder.button(
            text=label,
            callback_data=VariantCallback(product_id=product_id, variant_id=variant.get("id")),
        )
    builder.button(text="⬅️ Назад", callback_data=MenuCallback(action="catalog"))
    builder.adjust(1)
    return builder


def purchases_kb(purchases: list[dict]) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for purchase in purchases:
        status = purchase.get("status")
        title = purchase.get("product_title", "Товар")
        text = f"{title} · {status}"
        token_url = purchase.get("token_url")
        invoice_url = purchase.get("invoice_url")
        if token_url:
            builder.button(text=f"Получить {title}", url=token_url)
        elif invoice_url:
            builder.button(text=f"Оплатить {title}", url=invoice_url)
        builder.button(
            text=text,
            callback_data=PurchaseCallback(action="noop", purchase_id=purchase.get("id")),
        )
    builder.button(text="⬅️ Назад", callback_data=MenuCallback(action="back_main"))
    builder.adjust(1)
    return builder


def support_button(username: str | None) -> InlineKeyboardMarkup:
    button = InlineKeyboardButton(
        text="Поддержка",
        url=f"https://t.me/{(username or '').lstrip('@') or 'support'}",
    )
    return InlineKeyboardMarkup(inline_keyboard=[[button]])
