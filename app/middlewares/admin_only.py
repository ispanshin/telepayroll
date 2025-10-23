from __future__ import annotations
from typing import Any, Awaitable, Callable, Dict, Iterable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class AdminOnlyMiddleware(BaseMiddleware):
    def __init__(self, admin_ids: Iterable[int]):
        # нормализуем в множество для O(1)
        self._admins = {int(x) for x in admin_ids}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        user_id = int(user.id) if user else None

        if user_id is None or user_id not in self._admins:
            # блокируем доступ (не зовём handler)
            return

        return await handler(event, data)
