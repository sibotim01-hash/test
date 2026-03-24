from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from database.db import get_all_user_ids
from keyboards.keyboards import admin_menu_kb
from utils.states import BroadcastState
from utils.helpers import is_admin

router = Router()


@router.message(F.text == "📢 Xabarnoma")
async def start_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(BroadcastState.waiting_content)
    await message.answer(
        "📢 <b>Xabarnoma yuborish</b>\n\n"
        "Barcha foydalanuvchilarga yuboriladigan xabar yoki rasm+matn yuboring.\n\n"
        "<i>Bekor qilish uchun /cancel yuboring</i>"
    )


@router.message(BroadcastState.waiting_content, F.text == "/cancel")
async def cancel_broadcast(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Xabarnoma bekor qilindi.", reply_markup=admin_menu_kb())


@router.message(BroadcastState.waiting_content)
async def receive_broadcast_content(message: Message, state: FSMContext):
    # Ma'lumotlarni saqlash
    data = {}
    if message.photo:
        data["photo_id"] = message.photo[-1].file_id
        data["caption"] = message.caption or ""
        data["content_type"] = "photo"
    elif message.text:
        data["text"] = message.text
        data["content_type"] = "text"
    else:
        await message.answer("❌ Faqat matn yoki rasm+matn yuboring.")
        return

    await state.update_data(**data)
    await state.set_state(BroadcastState.confirm)

    # Tasdiqlash so'rash
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Yuborish", callback_data="confirm_broadcast"),
        InlineKeyboardButton(text="❌ Bekor", callback_data="cancel_broadcast")
    )

    user_count = len(await get_all_user_ids())
    await message.answer(
        f"📤 <b>Xabarnomani yuborishni tasdiqlaysizmi?</b>\n\n"
        f"👥 {user_count} ta foydalanuvchiga yuboriladi.",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "confirm_broadcast")
async def execute_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    data = await state.get_data()
    await state.clear()

    user_ids = await get_all_user_ids()
    bot: Bot = callback.bot

    success = 0
    failed = 0

    await callback.message.edit_text(f"📤 Yuborilmoqda... ({len(user_ids)} ta)")

    for user_id in user_ids:
        try:
            if data.get("content_type") == "photo":
                await bot.send_photo(
                    chat_id=user_id,
                    photo=data["photo_id"],
                    caption=data.get("caption", "")
                )
            else:
                await bot.send_message(chat_id=user_id, text=data["text"])
            success += 1
        except Exception:
            failed += 1

    await callback.message.answer(
        f"✅ <b>Xabarnoma yuborildi!</b>\n\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Xatolik: {failed}",
        reply_markup=admin_menu_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_broadcast")
async def cancel_broadcast_cb(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Xabarnoma bekor qilindi.")
    await callback.answer()
