from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from database.db import add_user
from keyboards.keyboards import main_menu_kb, admin_menu_kb
from utils.helpers import is_admin

router = Router()

CONTACT_TEXT = """📞 <b>Bog'lanish ma'lumotlari</b>

🏪 <b>Asbob-Uskunalar Do'koni</b>

📍 Manzil: Toshkent sh., Chilonzor t.
🕐 Ish vaqti: 09:00 – 19:00 (Dushanba-Shanba)
📱 Telefon: +998 90 123 45 67
📱 Telefon: +998 71 234 56 78
💬 Telegram: @asbob_admin
"""

INFO_TEXT = """ℹ️ <b>Do'kon haqida</b>

🔧 Bizda siz topasiz:
• Makita, Dewalt, Bosch, Hilti va boshqa brendlarning original asboblarini
• Professional va uy-ro'zg'or uchun uskuna va jihozlarni
• Ehtiyot qismlar va aksessuarlarni

✅ <b>Afzalliklarimiz:</b>
• 100% original mahsulotlar
• Kafolat va servis xizmati
• Tez yetkazib berish
• Qulay narxlar

📦 Buyurtma berish uchun katalogdan mahsulot tanlang va savatga qo'shing!
"""


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    await add_user(user.id, user.username or "", user.full_name)

    welcome = f"👋 Salom, <b>{user.full_name}</b>!\n\n"
    welcome += "🔧 <b>Asbob-Uskunalar Do'koniga</b> xush kelibsiz!\n\n"
    welcome += "Quyidagi menyu orqali xizmatlarimizdan foydalaning:"

    if is_admin(user.id):
        await message.answer(welcome, reply_markup=main_menu_kb())
        await message.answer(
            "⚙️ <b>Admin panelga kirish uchun</b> /admin buyrug'idan foydalaning."
        )
    else:
        await message.answer(welcome, reply_markup=main_menu_kb())


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    await state.clear()
    await message.answer(
        "⚙️ <b>Admin Panel</b>\n\nNimani boshqarmoqchisiz?",
        reply_markup=admin_menu_kb()
    )


@router.message(F.text == "🚪 Chiqish")
async def exit_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=main_menu_kb())


@router.message(F.text == "📞 Bog'lanish")
async def contact_info(message: Message):
    await message.answer(CONTACT_TEXT)


@router.message(F.text == "ℹ️ Ma'lumot")
async def bot_info(message: Message):
    await message.answer(INFO_TEXT)
