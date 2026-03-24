import asyncio
import logging
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


async def run_bot(bot, dp):
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def main():
    await init_db()

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

    config = uvicorn.Config(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="warning",
        loop="asyncio"
    )
    server = uvicorn.Server(config)

    logger.info("Bot va API ishga tushmoqda...")
    await asyncio.gather(
        server.serve(),
        run_bot(bot, dp)
    )


if __name__ == "__main__":
    asyncio.run(main())
