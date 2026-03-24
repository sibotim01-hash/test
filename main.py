import asyncio
import logging
import threading
import uvicorn

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database.db import init_db
from handlers import user, catalog, cart, admin, broadcast

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_api():
    import os
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        log_level="warning"
    )


async def run_bot():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(admin.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(broadcast.router)
    dp.include_router(user.router)

    await init_db()

    logger.info("Bot ishga tushmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def main():
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    logger.info("FastAPI ishga tushdi")
    await run_bot()


if __name__ == "__main__":
    asyncio.run(main())
