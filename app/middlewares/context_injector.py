from __future__ import annotations
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from ..context import AppContext

class ContextInjector(BaseMiddleware):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx = ctx

    async def __call__(self, handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]], event: Any, data: Dict[str, Any]) -> Any:
        data["ctx"] = self._ctx
        return await handler(event, data)
