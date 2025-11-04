from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from .config import settings
from .handlers import start

logging.basicConfig(level=logging.INFO)


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(start.router)
    return dp


async def main() -> None:
    bot = Bot(token=settings.telegram_bot_token, parse_mode=ParseMode.HTML)
    dp = create_dispatcher()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
