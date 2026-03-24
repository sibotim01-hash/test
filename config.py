import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///asbob_bot.db")

# Rasm saqlash papkasi
MEDIA_DIR = "media/products"
os.makedirs(MEDIA_DIR, exist_ok=True)
