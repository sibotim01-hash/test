from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.db import (
    get_brands, get_categories, get_products, get_sale_products
)
from keyboards.keyboards import (
    brands_kb, categories_kb, back_kb, main_menu_kb, product_inline_kb
)
from utils.states import CatalogState
from utils.helpers import format_product_text

router = Router()


@router.message(F.text == "🛍 Katalog")
async def show_catalog(message: Message, state: FSMContext):
    brands = await get_brands()
    if not brands:
        await message.answer("😔 Hozircha katalog bo'sh. Tez orada to'ldiriladi!")
        return
    await state.set_state(CatalogState.choosing_brand)
    await message.answer(
        "🏭 <b>Brendni tanlang:</b>",
        reply_markup=brands_kb(brands)
    )


@router.message(F.text == "🏷 Aksiyalar")
async def show_sales(message: Message):
    products = await get_sale_products()
    if not products:
        await message.answer("😔 Hozircha aksiyalar mavjud emas.")
        return
    await message.answer(f"🏷 <b>Aksiyali mahsulotlar ({len(products)} ta):</b>")
    for product in products:
        caption = f"🏷 <b>AKSIYA!</b>\n"
        caption += f"🏭 {product['brand_name']} | 📂 {product['cat_name']}\n\n"
        caption += format_product_text(product)
        if product["photo_id"]:
            await message.answer_photo(
                photo=product["photo_id"],
                caption=caption,
                reply_markup=product_inline_kb(product["id"])
            )
        else:
            await message.answer(caption, reply_markup=product_inline_kb(product["id"]))


@router.message(CatalogState.choosing_brand)
async def choose_brand(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("🏠 Asosiy menyu", reply_markup=main_menu_kb())
        return

    # Emoji + nom formatidan nom ajratish
    brand_name = message.text
    for emoji in ["🔧", "⚙️", "🔨", "🛠", "🔩", "🔌", "💡", "🏭"]:
        brand_name = brand_name.replace(f"{emoji} ", "").strip()

    # Brendlar ro'yxatidan mosini topish
    brands = await get_brands()
    selected_brand = None
    for brand in brands:
        if message.text == f"{brand['emoji']} {brand['name']}" or message.text == brand['name']:
            selected_brand = brand
            break

    if not selected_brand:
        await message.answer("❌ Brend topilmadi. Iltimos, ro'yxatdan tanlang.")
        return

    categories = await get_categories(selected_brand["id"])
    if not categories:
        await message.answer("😔 Bu brendda hozircha mahsulotlar yo'q.")
        return

    await state.update_data(brand_id=selected_brand["id"], brand_name=selected_brand["name"])
    await state.set_state(CatalogState.choosing_category)
    await message.answer(
        f"📂 <b>{selected_brand['name']}</b> - kategoriyani tanlang:",
        reply_markup=categories_kb(categories)
    )


@router.message(CatalogState.choosing_category)
async def choose_category(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        brands = await get_brands()
        await state.set_state(CatalogState.choosing_brand)
        await message.answer("🏭 Brendni tanlang:", reply_markup=brands_kb(brands))
        return

    data = await state.get_data()
    brand_id = data.get("brand_id")
    brand_name = data.get("brand_name")

    categories = await get_categories(brand_id)
    selected_cat = None
    for cat in categories:
        if message.text == f"{cat['emoji']} {cat['name']}" or message.text == cat['name']:
            selected_cat = cat
            break

    if not selected_cat:
        await message.answer("❌ Kategoriya topilmadi. Iltimos, ro'yxatdan tanlang.")
        return

    products = await get_products(selected_cat["id"])
    if not products:
        await message.answer("😔 Bu kategoriyada hozircha mahsulotlar yo'q.")
        return

    await state.update_data(category_id=selected_cat["id"])
    await state.set_state(CatalogState.viewing_products)

    await message.answer(
        f"📦 <b>{brand_name} → {selected_cat['name']}</b>\n"
        f"Jami: {len(products)} ta mahsulot",
        reply_markup=back_kb()
    )

    for product in products:
        caption = format_product_text(product)
        if product["photo_id"]:
            await message.answer_photo(
                photo=product["photo_id"],
                caption=caption,
                reply_markup=product_inline_kb(product["id"])
            )
        else:
            await message.answer(caption, reply_markup=product_inline_kb(product["id"]))


@router.message(CatalogState.viewing_products, F.text == "🔙 Orqaga")
async def back_to_categories(message: Message, state: FSMContext):
    data = await state.get_data()
    brand_id = data.get("brand_id")
    brand_name = data.get("brand_name")
    categories = await get_categories(brand_id)
    await state.set_state(CatalogState.choosing_category)
    await message.answer(
        f"📂 <b>{brand_name}</b> - kategoriyani tanlang:",
        reply_markup=categories_kb(categories)
    )
