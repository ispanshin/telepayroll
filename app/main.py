from __future__ import annotations
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from .config import Settings
from .context import AppContext
from .middlewares.context_injector import ContextInjector
from .handlers import common as common_handlers
from .handlers import informatics as informatics_handlers
from .handlers import payroll as payroll_handlers
from .handlers import roster as roster_handlers


async def main():
    load_dotenv()
    settings = Settings()
    bot = Bot(settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())

    ctx = AppContext.build(bot=bot, settings=settings)
    # глобальный инжектор контекста
    dp.message.middleware(ContextInjector(ctx))
    dp.callback_query.middleware(ContextInjector(ctx))
    dp.poll_answer.middleware(ContextInjector(ctx))

    # роутеры
    dp.include_router(common_handlers.router)
    dp.include_router(informatics_handlers.router)
    dp.include_router(payroll_handlers.router)
    dp.include_router(roster_handlers.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
