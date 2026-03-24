from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from database.db import (
    get_brands, get_categories, get_all_categories, get_all_products,
    add_brand, delete_brand, add_category, delete_category,
    add_product, delete_product, update_product_price,
    get_user_count, get_product
)
from keyboards.keyboards import (
    admin_menu_kb, admin_brands_kb, admin_categories_kb, admin_products_kb,
    admin_product_manage_kb, select_brand_for_cat_kb, select_brand_for_prod_kb,
    select_cat_for_prod_kb, confirm_delete_kb, back_kb
)
from utils.states import AdminState
from utils.helpers import is_admin, format_price

router = Router()


def admin_filter(message: Message) -> bool:
    return is_admin(message.from_user.id)


# ════════════════════════════════════════
#           BRENDLAR BOSHQARUVI
# ════════════════════════════════════════

@router.message(F.text == "🏷 Brendlar")
async def admin_brands(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    brands = await get_brands()
    text = f"🏷 <b>Brendlar</b> ({len(brands)} ta):"
    if not brands:
        text += "\n\nHali brend qo'shilmagan."
    await message.answer(text, reply_markup=admin_brands_kb(brands))


@router.callback_query(F.data == "add_brand")
async def start_add_brand(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminState.add_brand_name)
    await callback.message.answer(
        "📝 Yangi brend nomini kiriting:\n<i>(Masalan: Makita, Dewalt, Bosch)</i>",
        reply_markup=back_kb()
    )
    await callback.answer()


@router.message(AdminState.add_brand_name)
async def get_brand_name(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Admin panel", reply_markup=admin_menu_kb())
        return
    await state.update_data(brand_name=message.text.strip())
    await state.set_state(AdminState.add_brand_emoji)
    await message.answer(
        "😊 Brend uchun emoji kiriting:\n<i>(Masalan: 🔧 yoki ⚙️)</i>\n"
        "Yoki <b>skip</b> deb yuboring (standart: 🔧)"
    )


@router.message(AdminState.add_brand_emoji)
async def get_brand_emoji(message: Message, state: FSMContext):
    data = await state.get_data()
    brand_name = data.get("brand_name")
    emoji = message.text.strip() if message.text.lower() != "skip" else "🔧"

    success = await add_brand(brand_name, emoji)
    await state.clear()

    if success:
        await message.answer(
            f"✅ <b>{emoji} {brand_name}</b> brendi muvaffaqiyatli qo'shildi!",
            reply_markup=admin_menu_kb()
        )
    else:
        await message.answer(
            f"❌ Bu brend allaqachon mavjud!",
            reply_markup=admin_menu_kb()
        )


@router.callback_query(F.data.startswith("del_brand:"))
async def confirm_del_brand(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    brand_id = int(callback.data.split(":")[1])
    await callback.message.answer(
        "⚠️ <b>Brendni o'chirishni tasdiqlaysizmi?</b>\n"
        "Bu brendga bog'liq barcha kategoriya va mahsulotlar ham o'chiriladi!",
        reply_markup=confirm_delete_kb("brand", brand_id)
    )
    await callback.answer()


# ════════════════════════════════════════
#           KATEGORIYALAR BOSHQARUVI
# ════════════════════════════════════════

@router.message(F.text == "📂 Kategoriyalar")
async def admin_categories(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    categories = await get_all_categories()
    text = f"📂 <b>Kategoriyalar</b> ({len(categories)} ta):"
    await message.answer(text, reply_markup=admin_categories_kb(categories))


@router.callback_query(F.data == "add_category")
async def start_add_category(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    brands = await get_brands()
    if not brands:
        await callback.answer("❌ Avval brend qo'shing!", show_alert=True)
        return
    await state.set_state(AdminState.add_cat_brand)
    await callback.message.answer(
        "🏭 Qaysi brendga kategoriya qo'shmoqchisiz?",
        reply_markup=select_brand_for_cat_kb(brands)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sel_brand_cat:"), AdminState.add_cat_brand)
async def sel_brand_for_cat(callback: CallbackQuery, state: FSMContext):
    brand_id = int(callback.data.split(":")[1])
    await state.update_data(brand_id=brand_id)
    await state.set_state(AdminState.add_cat_name)
    await callback.message.answer(
        "📝 Kategoriya nomini kiriting:\n<i>(Masalan: Perforatorlar, Bolgarkalar)</i>"
    )
    await callback.answer()


@router.message(AdminState.add_cat_name)
async def get_cat_name(message: Message, state: FSMContext):
    await state.update_data(cat_name=message.text.strip())
    await state.set_state(AdminState.add_cat_emoji)
    await message.answer(
        "😊 Kategoriya emojisi:\n<i>(Masalan: 🔨 yoki 📦)</i>\n"
        "Yoki <b>skip</b> (standart: 📦)"
    )


@router.message(AdminState.add_cat_emoji)
async def get_cat_emoji(message: Message, state: FSMContext):
    data = await state.get_data()
    emoji = message.text.strip() if message.text.lower() != "skip" else "📦"
    success = await add_category(data["brand_id"], data["cat_name"], emoji)
    await state.clear()

    if success:
        await message.answer(
            f"✅ <b>{emoji} {data['cat_name']}</b> kategoriyasi qo'shildi!",
            reply_markup=admin_menu_kb()
        )
    else:
        await message.answer("❌ Xatolik yuz berdi!", reply_markup=admin_menu_kb())


@router.callback_query(F.data.startswith("del_cat:"))
async def confirm_del_cat(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    cat_id = int(callback.data.split(":")[1])
    await callback.message.answer(
        "⚠️ Kategoriyani o'chirishni tasdiqlaysizmi?",
        reply_markup=confirm_delete_kb("cat", cat_id)
    )
    await callback.answer()


# ════════════════════════════════════════
#           MAHSULOTLAR BOSHQARUVI
# ════════════════════════════════════════

@router.message(F.text == "📦 Mahsulotlar")
async def admin_products(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    products = await get_all_products()
    text = f"📦 <b>Mahsulotlar</b> ({len(products)} ta):"
    await message.answer(text, reply_markup=admin_products_kb(products))


@router.callback_query(F.data == "add_product")
async def start_add_product(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    brands = await get_brands()
    if not brands:
        await callback.answer("❌ Avval brend qo'shing!", show_alert=True)
        return
    await state.set_state(AdminState.add_prod_brand)
    await callback.message.answer(
        "🏭 Brendni tanlang:",
        reply_markup=select_brand_for_prod_kb(brands)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sel_brand_prod:"), AdminState.add_prod_brand)
async def sel_brand_for_prod(callback: CallbackQuery, state: FSMContext):
    brand_id = int(callback.data.split(":")[1])
    categories = await get_categories(brand_id)
    if not categories:
        await callback.answer("❌ Bu brendda kategoriya yo'q!", show_alert=True)
        return
    await state.update_data(brand_id=brand_id)
    await state.set_state(AdminState.add_prod_cat)
    await callback.message.answer(
        "📂 Kategoriyani tanlang:",
        reply_markup=select_cat_for_prod_kb(categories)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sel_cat_prod:"), AdminState.add_prod_cat)
async def sel_cat_for_prod(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split(":")[1])
    await state.update_data(category_id=cat_id)
    await state.set_state(AdminState.add_prod_name)
    await callback.message.answer("📝 Mahsulot nomini kiriting:")
    await callback.answer()


@router.message(AdminState.add_prod_name)
async def get_prod_name(message: Message, state: FSMContext):
    await state.update_data(prod_name=message.text.strip())
    await state.set_state(AdminState.add_prod_desc)
    await message.answer(
        "📄 Mahsulot tavsifini kiriting:\n<i>(Yoki <b>skip</b> yuboring)</i>"
    )


@router.message(AdminState.add_prod_desc)
async def get_prod_desc(message: Message, state: FSMContext):
    desc = "" if message.text.lower() == "skip" else message.text.strip()
    await state.update_data(prod_desc=desc)
    await state.set_state(AdminState.add_prod_price)
    await message.answer("💰 Narxini kiriting (so'mda, faqat raqam):\n<i>Masalan: 1250000</i>")


@router.message(AdminState.add_prod_price)
async def get_prod_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(" ", "").replace(",", ""))
        await state.update_data(prod_price=price)
        await state.set_state(AdminState.add_prod_photo)
        await message.answer(
            "🖼 Mahsulot rasmini yuboring:\n<i>(Yoki <b>skip</b> yuboring)</i>"
        )
    except ValueError:
        await message.answer("❌ Narx noto'g'ri! Faqat raqam kiriting.")


@router.message(AdminState.add_prod_photo)
async def get_prod_photo(message: Message, state: FSMContext):
    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await state.set_state(AdminState.add_prod_sale)
    await message.answer(
        "🏷 Bu mahsulot aksiyada bormi?\n"
        "<b>ha</b> yoki <b>yo'q</b> yuboring:"
    )


@router.message(AdminState.add_prod_sale)
async def get_prod_sale(message: Message, state: FSMContext):
    is_sale = 1 if message.text.lower() in ["ha", "yes", "1"] else 0
    await state.update_data(is_sale=is_sale)

    if is_sale:
        await state.set_state(AdminState.add_prod_old_price)
        await message.answer("💰 Eski (chegirmadan oldingi) narxni kiriting:")
    else:
        await finish_add_product(message, state)


@router.message(AdminState.add_prod_old_price)
async def get_prod_old_price(message: Message, state: FSMContext):
    try:
        old_price = float(message.text.replace(" ", "").replace(",", ""))
        await state.update_data(old_price=old_price)
        await finish_add_product(message, state)
    except ValueError:
        await message.answer("❌ Narx noto'g'ri!")


async def finish_add_product(message: Message, state: FSMContext):
    data = await state.get_data()
    await add_product(
        brand_id=data["brand_id"],
        category_id=data["category_id"],
        name=data["prod_name"],
        description=data.get("prod_desc", ""),
        price=data["prod_price"],
        photo_id=data.get("photo_id"),
        is_sale=data.get("is_sale", 0),
        old_price=data.get("old_price")
    )
    await state.clear()
    await message.answer(
        f"✅ <b>{data['prod_name']}</b> mahsuloti muvaffaqiyatli qo'shildi!",
        reply_markup=admin_menu_kb()
    )


# ─── Mahsulotni boshqarish ───
@router.callback_query(F.data.startswith("admin_prod:"))
async def manage_product(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    product_id = int(callback.data.split(":")[1])
    product = await get_product(product_id)
    if not product:
        await callback.answer("Mahsulot topilmadi!", show_alert=True)
        return
    text = (
        f"📦 <b>{product['name']}</b>\n"
        f"💰 Narx: {format_price(product['price'])}\n"
        f"🏷 Aksiya: {'Ha' if product['is_sale'] else 'Yo\'q'}"
    )
    await callback.message.answer(text, reply_markup=admin_product_manage_kb(product_id))
    await callback.answer()


@router.callback_query(F.data.startswith("edit_price:"))
async def start_edit_price(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    product_id = int(callback.data.split(":")[1])
    await state.set_state(AdminState.edit_price_value)
    await state.update_data(edit_product_id=product_id)
    await callback.message.answer("💰 Yangi narxni kiriting (so'mda):")
    await callback.answer()


@router.message(AdminState.edit_price_value)
async def save_new_price(message: Message, state: FSMContext):
    try:
        new_price = float(message.text.replace(" ", "").replace(",", ""))
        data = await state.get_data()
        await update_product_price(data["edit_product_id"], new_price)
        await state.clear()
        await message.answer(
            f"✅ Narx {format_price(new_price)} ga yangilandi!",
            reply_markup=admin_menu_kb()
        )
    except ValueError:
        await message.answer("❌ Noto'g'ri narx! Faqat raqam kiriting.")


@router.callback_query(F.data.startswith("del_product:"))
async def confirm_del_product(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    product_id = int(callback.data.split(":")[1])
    await callback.message.answer(
        "⚠️ Mahsulotni o'chirishni tasdiqlaysizmi?",
        reply_markup=confirm_delete_kb("product", product_id)
    )
    await callback.answer()


# ─── O'chirishni tasdiqlash ───
@router.callback_query(F.data.startswith("confirm_del:"))
async def execute_delete(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    parts = callback.data.split(":")
    item_type, item_id = parts[1], int(parts[2])

    if item_type == "brand":
        await delete_brand(item_id)
        await callback.message.edit_text("✅ Brend o'chirildi.")
    elif item_type == "cat":
        await delete_category(item_id)
        await callback.message.edit_text("✅ Kategoriya o'chirildi.")
    elif item_type == "product":
        await delete_product(item_id)
        await callback.message.edit_text("✅ Mahsulot o'chirildi.")
    await callback.answer("O'chirildi!")


@router.callback_query(F.data == "cancel_del")
async def cancel_delete(callback: CallbackQuery):
    await callback.message.edit_text("❌ O'chirish bekor qilindi.")
    await callback.answer()


@router.callback_query(F.data == "back_products")
async def back_to_products(callback: CallbackQuery):
    products = await get_all_products()
    await callback.message.answer(
        f"📦 <b>Mahsulotlar</b> ({len(products)} ta):",
        reply_markup=admin_products_kb(products)
    )
    await callback.answer()


# ════════════════════════════════════════
#           STATISTIKA
# ════════════════════════════════════════

@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    user_count = await get_user_count()
    products = await get_all_products()
    brands = await get_brands()
    categories = await get_all_categories()
    sale_products = [p for p in products if p["is_sale"]]

    text = (
        f"📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{user_count}</b>\n"
        f"🏭 Brendlar: <b>{len(brands)}</b>\n"
        f"📂 Kategoriyalar: <b>{len(categories)}</b>\n"
        f"📦 Mahsulotlar: <b>{len(products)}</b>\n"
        f"🏷 Aksiyali mahsulotlar: <b>{len(sale_products)}</b>"
    )
    await message.answer(text)


# ─── Kategoriya/brend fetch uchun helper ─── (katalog handlerdagi import uchun)
async def get_categories(brand_id):
    from database.db import get_categories as _get_cats
    return await _get_cats(brand_id)
