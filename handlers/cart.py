from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS
from database.db import (
    add_to_cart, get_cart, remove_from_cart, clear_cart,
    update_cart_quantity, create_order, get_product,
    update_user_phone, get_all_user_ids
)
from keyboards.keyboards import (
    main_menu_kb, cart_item_kb, checkout_kb,
    contact_location_kb, location_kb, confirm_order_kb
)
from utils.states import CartState
from utils.helpers import format_price

router = Router()


# ─── Savatga qo'shish ───
@router.callback_query(F.data.startswith("add_cart:"))
async def add_to_cart_cb(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    await add_to_cart(callback.from_user.id, product_id)
    product = await get_product(product_id)
    await callback.answer(f"✅ '{product['name']}' savatga qo'shildi!", show_alert=False)


# ─── Savatcha ko'rish ───
@router.message(F.text == "🛒 Savatcha")
async def show_cart(message: Message, state: FSMContext):
    await state.clear()
    cart_items = await get_cart(message.from_user.id)

    if not cart_items:
        await message.answer(
            "🛒 Savatchangiz bo'sh.\n\nMahsulot qo'shish uchun Katalogga o'ting.",
            reply_markup=main_menu_kb()
        )
        return

    total = sum(item["price"] * item["quantity"] for item in cart_items)
    await message.answer(
        f"🛒 <b>Savatchangiz</b> ({len(cart_items)} xil mahsulot):\n"
        f"💰 Jami: <b>{format_price(total)}</b>",
        reply_markup=checkout_kb()
    )

    for item in cart_items:
        item_total = item["price"] * item["quantity"]
        text = (
            f"📦 <b>{item['name']}</b>\n"
            f"💰 {format_price(item['price'])} × {item['quantity']} = "
            f"<b>{format_price(item_total)}</b>"
        )
        await message.answer(text, reply_markup=cart_item_kb(item["id"], item["quantity"]))


# ─── Miqdor o'zgartirish ───
@router.callback_query(F.data.startswith("cart_plus:"))
async def cart_plus(callback: CallbackQuery):
    cart_id = int(callback.data.split(":")[1])
    cart = await get_cart(callback.from_user.id)
    item = next((i for i in cart if i["id"] == cart_id), None)
    if item:
        new_qty = item["quantity"] + 1
        await update_cart_quantity(cart_id, new_qty)
        item_total = item["price"] * new_qty
        text = (
            f"📦 <b>{item['name']}</b>\n"
            f"💰 {format_price(item['price'])} × {new_qty} = "
            f"<b>{format_price(item_total)}</b>"
        )
        await callback.message.edit_text(text, reply_markup=cart_item_kb(cart_id, new_qty))
    await callback.answer()


@router.callback_query(F.data.startswith("cart_minus:"))
async def cart_minus(callback: CallbackQuery):
    cart_id = int(callback.data.split(":")[1])
    cart = await get_cart(callback.from_user.id)
    item = next((i for i in cart if i["id"] == cart_id), None)
    if item:
        new_qty = item["quantity"] - 1
        if new_qty <= 0:
            await remove_from_cart(cart_id)
            await callback.message.delete()
            await callback.answer("🗑 Mahsulot savatdan o'chirildi.")
        else:
            await update_cart_quantity(cart_id, new_qty)
            item_total = item["price"] * new_qty
            text = (
                f"📦 <b>{item['name']}</b>\n"
                f"💰 {format_price(item['price'])} × {new_qty} = "
                f"<b>{format_price(item_total)}</b>"
            )
            await callback.message.edit_text(text, reply_markup=cart_item_kb(cart_id, new_qty))
            await callback.answer()


@router.callback_query(F.data.startswith("cart_remove:"))
async def cart_remove(callback: CallbackQuery):
    cart_id = int(callback.data.split(":")[1])
    await remove_from_cart(cart_id)
    await callback.message.delete()
    await callback.answer("🗑 O'chirildi.")


@router.callback_query(F.data == "cart_noop")
async def cart_noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data == "clear_cart")
async def clear_cart_cb(callback: CallbackQuery):
    await clear_cart(callback.from_user.id)
    await callback.message.edit_text("🗑 Savatcha tozalandi.")
    await callback.answer("✅ Savatcha tozalandi!")


# ─── Buyurtma boshlash ───
@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    cart_items = await get_cart(callback.from_user.id)
    if not cart_items:
        await callback.answer("😔 Savatcha bo'sh!", show_alert=True)
        return

    total = sum(item["price"] * item["quantity"] for item in cart_items)
    items_data = [
        {
            "product_id": item["product_id"],
            "name": item["name"],
            "price": item["price"],
            "quantity": item["quantity"]
        }
        for item in cart_items
    ]
    await state.update_data(order_items=items_data, total=total)
    await state.set_state(CartState.waiting_contact)

    await callback.message.answer(
        "📱 <b>Buyurtmani rasmiylashtirish</b>\n\n"
        "Telefon raqamingizni yuboring (tugmani bosing):",
        reply_markup=contact_location_kb()
    )
    await callback.answer()


# ─── Kontakt qabul qilish ───
@router.message(CartState.waiting_contact, F.contact)
async def get_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    await update_user_phone(message.from_user.id, phone)
    await state.update_data(
        phone=phone,
        full_name=message.from_user.full_name
    )
    await state.set_state(CartState.waiting_location)
    await message.answer(
        "📍 <b>Lokatsiyangizni yuboring</b>\n\n"
        "Bu yetkazib berish uchun kerak bo'ladi. "
        "Yoki lokatsiyasiz davom etishingiz mumkin:",
        reply_markup=location_kb()
    )


@router.message(CartState.waiting_contact, F.text == "❌ Bekor qilish")
async def cancel_checkout_contact(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Buyurtma bekor qilindi.", reply_markup=main_menu_kb())


# ─── Lokatsiya qabul qilish ───
@router.message(CartState.waiting_location, F.location)
async def get_location(message: Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    await state.update_data(lat=lat, lon=lon)
    await show_order_confirmation(message, state)


@router.message(CartState.waiting_location, F.text == "⏭ Lokatsiyasiz davom etish")
async def skip_location(message: Message, state: FSMContext):
    await state.update_data(lat=None, lon=None)
    await show_order_confirmation(message, state)


@router.message(CartState.waiting_location, F.text == "❌ Bekor qilish")
async def cancel_checkout_location(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Buyurtma bekor qilindi.", reply_markup=main_menu_kb())


async def show_order_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    items = data.get("order_items", [])
    total = data.get("total", 0)
    phone = data.get("phone")

    text = "📋 <b>Buyurtma tafsilotlari:</b>\n\n"
    for item in items:
        text += f"• {item['name']} × {item['quantity']} = {format_price(item['price'] * item['quantity'])}\n"
    text += f"\n💰 <b>Jami: {format_price(total)}</b>"
    text += f"\n📱 Telefon: {phone}"
    text += "\n\nBuyurtmani tasdiqlaysizmi?"

    await state.set_state(CartState.confirming)
    await message.answer(text, reply_markup=confirm_order_kb())


# ─── Buyurtmani tasdiqlash ───
@router.message(CartState.confirming, F.text == "✅ Buyurtmani tasdiqlash")
async def confirm_order(message: Message, state: FSMContext):
    data = await state.get_data()
    items = data.get("order_items", [])
    total = data.get("total", 0)
    phone = data.get("phone")
    full_name = data.get("full_name", message.from_user.full_name)
    lat = data.get("lat")
    lon = data.get("lon")

    order_id = await create_order(
        user_id=message.from_user.id,
        full_name=full_name,
        phone=phone,
        lat=lat, lon=lon,
        total=total,
        items=items
    )

    await clear_cart(message.from_user.id)
    await state.clear()

    await message.answer(
        f"✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
        f"📌 Buyurtma raqami: <b>#{order_id}</b>\n"
        f"💰 Jami: <b>{format_price(total)}</b>\n\n"
        f"Tez orada operator siz bilan bog'lanadi. Rahmat! 🙏",
        reply_markup=main_menu_kb()
    )

    # Adminga xabarnoma yuborish
    bot = message.bot
    admin_text = (
        f"🆕 <b>YANGI BUYURTMA #{order_id}</b>\n\n"
        f"👤 Mijoz: {full_name}\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"📱 Telefon: {phone}\n"
        f"🔗 Username: @{message.from_user.username or 'yo\'q'}\n\n"
        f"📦 <b>Mahsulotlar:</b>\n"
    )
    for item in items:
        admin_text += f"• {item['name']} × {item['quantity']} = {format_price(item['price'] * item['quantity'])}\n"
    admin_text += f"\n💰 <b>Jami: {format_price(total)}</b>"

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text)
            if lat and lon:
                await bot.send_location(admin_id, latitude=lat, longitude=lon)
        except Exception:
            pass


@router.message(CartState.confirming, F.text == "❌ Bekor qilish")
async def cancel_order(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Buyurtma bekor qilindi.", reply_markup=main_menu_kb())
