from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from ..context import AppContext


class ContextInjector(BaseMiddleware):
    def __init__(self, ctx: AppContext):
        self._ctx = ctx

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data.setdefault("ctx", self._ctx)  # не трогаем, если кто-то уже положил
        return await handler(event, data)
