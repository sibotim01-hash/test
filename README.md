# 🔧 Asbob-Uskunalar Do'koni — Telegram Bot

Makita, Dewalt, Bosch va boshqa brendlarning mahsulotlarini Telegram orqali sotish uchun to'liq bot.

---

## 📦 Texnologiyalar

| Kutubxona | Versiya | Maqsad |
|-----------|---------|--------|
| aiogram | 3.13.1 | Telegram Bot Framework |
| aiosqlite | 0.20.0 | Asinxron SQLite |
| python-dotenv | 1.0.1 | .env faylini o'qish |

---

## 🗂 Loyiha strukturasi

```
asbob_bot/
├── main.py                  # Bot ishga tushirish nuqtasi
├── config.py                # Konfiguratsiya
├── requirements.txt
├── .env.example
│
├── database/
│   └── db.py               # SQLite jadvallar va barcha DB funksiyalari
│
├── handlers/
│   ├── user.py             # Start, asosiy menyu, ma'lumot, bog'lanish
│   ├── catalog.py          # Katalog: brend → kategoriya → mahsulotlar
│   ├── cart.py             # Savatcha va buyurtma berish
│   ├── admin.py            # Admin panel: CRUD
│   └── broadcast.py        # Xabarnoma yuborish
│
├── keyboards/
│   └── keyboards.py        # Barcha Reply va Inline klaviaturalar
│
└── utils/
    ├── states.py           # FSM holatlari
    └── helpers.py          # Yordamchi funksiyalar
```

---

## ⚙️ O'rnatish va ishga tushirish

### 1. Reponi klonlash yoki fayllarni yuklab olish

### 2. Virtual muhit yaratish
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 4. `.env` faylini sozlash
```bash
cp .env.example .env
```
`.env` faylini oching va quyidagilarni to'ldiring:
```env
BOT_TOKEN=7xxxxxxxxxx:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ADMIN_IDS=123456789
```
- `BOT_TOKEN` — [@BotFather](https://t.me/BotFather) dan olingan token
- `ADMIN_IDS` — Admin bo'ladigan Telegram ID(lar), vergul bilan ajratiladi

### 5. Botni ishga tushirish
```bash
python main.py
```

---

## 👤 Foydalanuvchi funksiyalari

| Tugma | Tavsif |
|-------|--------|
| 🛍 Katalog | Brend → Kategoriya → Mahsulotlar ro'yxati |
| 🏷 Aksiyalar | Chegirmadagi barcha mahsulotlar |
| 🛒 Savatcha | Savatni ko'rish, miqdor o'zgartirish, buyurtma berish |
| 📞 Bog'lanish | Do'kon manzili va telefon raqamlari |
| ℹ️ Ma'lumot | Do'kon haqida ma'lumot |

### Buyurtma berish jarayoni:
1. Mahsulotni savatga qo'shish (inline tugma)
2. 🛒 Savatcha → ✅ Buyurtma berish
3. Telefon raqamni yuborish (kontakt tugmasi)
4. Lokatsiya yuborish (yoki o'tkazib yuborish)
5. Buyurtmani tasdiqlash → Admin xabardor bo'ladi

---

## 🔑 Admin funksiyalari

Admin panelga kirish: `/admin` buyrug'i

| Tugma | Tavsif |
|-------|--------|
| 📦 Mahsulotlar | Barcha mahsulotlar ro'yxati, qo'shish, narx tahrirlash, o'chirish |
| 🏷 Brendlar | Brend qo'shish/o'chirish |
| 📂 Kategoriyalar | Kategoriya qo'shish/o'chirish |
| 📢 Xabarnoma | Barcha foydalanuvchilarga rasm/matn yuborish |
| 📊 Statistika | Foydalanuvchilar soni, mahsulotlar soni |

### Mahsulot qo'shish tartibi:
1. 📦 Mahsulotlar → ➕ Mahsulot qo'shish
2. Brendni tanlang
3. Kategoriyani tanlang
4. Nom → Tavsif → Narx → Rasm → Aksiyami?
5. Muvaffaqiyatli qo'shiladi!

---

## 🗄 Ma'lumotlar bazasi jadvallari

| Jadval | Tavsif |
|--------|--------|
| `users` | Foydalanuvchilar (ID, ism, telefon) |
| `brands` | Brendlar (Makita, Dewalt...) |
| `categories` | Kategoriyalar (brend bo'yicha) |
| `products` | Mahsulotlar (rasm, narx, aksiya) |
| `cart` | Savatcha (foydalanuvchi + mahsulot + miqdor) |
| `orders` | Buyurtmalar (telefon, lokatsiya, holat) |
| `order_items` | Buyurtma tarkibi |

---

## 🚀 Qo'shimcha imkoniyatlar

- ✅ Aksiyali mahsulotlar bo'limi
- ✅ Narxlarni admin panel orqali tahrirlash
- ✅ Rasm + matn bilan broadcast xabarnoma
- ✅ Buyurtmada lokatsiya yuborish
- ✅ Admin yangi buyurtma kelganda darhol xabar oladi
- ✅ Savatda miqdor ➕/➖ tugmalari

---

## 📝 Eslatmalar

- Bot faqat **SQLite** ishlatadi — alohida server kerak emas
- Rasmlar Telegram serverida saqlanadi (file_id orqali)
- Bir nechta admin bo'lishi mumkin (ADMIN_IDS da vergul bilan)
