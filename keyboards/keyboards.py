from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


# ════════════════════════════════════════
#           FOYDALANUVCHI KLAVIATURALARI
# ════════════════════════════════════════

def main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🛍 Katalog"),
        KeyboardButton(text="🏷 Aksiyalar")
    )
    builder.row(
        KeyboardButton(text="🛒 Savatcha"),
        KeyboardButton(text="📞 Bog'lanish")
    )
    builder.row(KeyboardButton(text="ℹ️ Ma'lumot"))
    return builder.as_markup(resize_keyboard=True)


def brands_kb(brands: list) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for brand in brands:
        builder.button(text=f"{brand['emoji']} {brand['name']}")
    builder.button(text="🔙 Orqaga")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def categories_kb(categories: list) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for cat in categories:
        builder.button(text=f"{cat['emoji']} {cat['name']}")
    builder.button(text="🔙 Orqaga")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def back_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔙 Orqaga")
    return builder.as_markup(resize_keyboard=True)


def contact_location_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True))
    builder.row(KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def location_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="📍 Lokatsiyamni yuborish", request_location=True))
    builder.row(KeyboardButton(text="⏭ Lokatsiyasiz davom etish"))
    builder.row(KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def confirm_order_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="✅ Buyurtmani tasdiqlash"))
    builder.row(KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)


# ════════════════════════════════════════
#           INLINE KLAVIATURALAR
# ════════════════════════════════════════

def product_inline_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Savatga qo'shish", callback_data=f"add_cart:{product_id}")
    return builder.as_markup()


def cart_item_kb(cart_id: int, quantity: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➖", callback_data=f"cart_minus:{cart_id}"),
        InlineKeyboardButton(text=f"{quantity} ta", callback_data="cart_noop"),
        InlineKeyboardButton(text="➕", callback_data=f"cart_plus:{cart_id}")
    )
    builder.row(InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"cart_remove:{cart_id}"))
    return builder.as_markup()


def checkout_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Buyurtma berish", callback_data="checkout")
    builder.button(text="🗑 Savatchani tozalash", callback_data="clear_cart")
    builder.adjust(1)
    return builder.as_markup()


# ════════════════════════════════════════
#           ADMIN KLAVIATURALARI
# ════════════════════════════════════════

def admin_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📦 Mahsulotlar"),
        KeyboardButton(text="🏷 Brendlar")
    )
    builder.row(
        KeyboardButton(text="📂 Kategoriyalar"),
        KeyboardButton(text="📢 Xabarnoma")
    )
    builder.row(
        KeyboardButton(text="📊 Statistika"),
        KeyboardButton(text="🚪 Chiqish")
    )
    return builder.as_markup(resize_keyboard=True)


def admin_brands_kb(brands: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for brand in brands:
        builder.row(
            InlineKeyboardButton(
                text=f"{brand['emoji']} {brand['name']}",
                callback_data=f"admin_brand:{brand['id']}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"del_brand:{brand['id']}"
            )
        )
    builder.row(InlineKeyboardButton(text="➕ Brend qo'shish", callback_data="add_brand"))
    return builder.as_markup()


def admin_categories_kb(categories: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.row(
            InlineKeyboardButton(
                text=f"{cat['emoji']} {cat['name']} ({cat['brand_name']})",
                callback_data=f"admin_cat:{cat['id']}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"del_cat:{cat['id']}"
            )
        )
    builder.row(InlineKeyboardButton(text="➕ Kategoriya qo'shish", callback_data="add_category"))
    return builder.as_markup()


def admin_products_kb(products: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in products:
        sale_icon = "🏷" if p["is_sale"] else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{sale_icon}{p['name']} - {p['price']:,.0f} so'm",
                callback_data=f"admin_prod:{p['id']}"
            )
        )
    builder.row(InlineKeyboardButton(text="➕ Mahsulot qo'shish", callback_data="add_product"))
    return builder.as_markup()


def admin_product_manage_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 Narxni o'zgartirish", callback_data=f"edit_price:{product_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"del_product:{product_id}"),
        InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_products")
    )
    return builder.as_markup()


def select_brand_for_cat_kb(brands: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for brand in brands:
        builder.button(
            text=f"{brand['emoji']} {brand['name']}",
            callback_data=f"sel_brand_cat:{brand['id']}"
        )
    builder.adjust(2)
    return builder.as_markup()


def select_brand_for_prod_kb(brands: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for brand in brands:
        builder.button(
            text=f"{brand['emoji']} {brand['name']}",
            callback_data=f"sel_brand_prod:{brand['id']}"
        )
    builder.adjust(2)
    return builder.as_markup()


def select_cat_for_prod_kb(categories: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=f"{cat['emoji']} {cat['name']}",
            callback_data=f"sel_cat_prod:{cat['id']}"
        )
    builder.adjust(2)
    return builder.as_markup()


def confirm_delete_kb(item_type: str, item_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"confirm_del:{item_type}:{item_id}"),
        InlineKeyboardButton(text="❌ Bekor", callback_data="cancel_del")
    )
    return builder.as_markup()
