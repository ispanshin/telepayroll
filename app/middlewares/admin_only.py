from __future__ import annotations
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

class AdminOnlyMiddleware(BaseMiddleware):
    def __init__(self, admin_ids: list[int]):
        super().__init__()
        self._admins = set(int(x) for x in admin_ids)

    async def __call__(self, handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]], event: Any, data: Dict[str, Any]) -> Any:
        user_id = None
        if hasattr(event, "from_user") and event.from_user:
            user_id = int(event.from_user.id)
        if user_id is None or user_id not in self._admins:
            # пропускаем — мы будем навешивать middleware только на отдельные роутеры
            return
        return await handler(event, data)
