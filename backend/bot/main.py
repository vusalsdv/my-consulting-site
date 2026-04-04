"""
Точка входа Telegram-бота.
Запуск: python -m bot.main  (из папки backend/)
"""

import asyncio
import logging
import os

import sentry_sdk
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .config import BOT_TOKEN
from .handlers import router
from .owner_commands import owner_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger(__name__)


async def main() -> None:
    if dsn := os.getenv("SENTRY_DSN"):
        sentry_sdk.init(dsn=dsn, environment=os.getenv("ENVIRONMENT", "production"))
        log.info("Sentry initialized")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    # owner_router первым — его команды приоритетнее
    dp.include_router(owner_router)
    dp.include_router(router)

    log.info("Bot starting (with job search module)...")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
