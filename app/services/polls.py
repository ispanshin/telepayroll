from __future__ import annotations

import asyncio
from typing import List
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from ..infra.repos.polls import PollsRepo, Poll
from ..infra.repos.settings import SettingsRepo


def _ensure_tyk(options: List[str]) -> List[str]:
    # добавим "Тык" (без учёта регистра/пробелов), если его ещё нет
    norm = [(o or "").strip() for o in options]
    has_tyk = any(o.lower() == "тык" for o in norm)
    return options if has_tyk else [*options, "Тык"]


class PollsService:
    def __init__(self, bot: Bot, polls: PollsRepo, conf: SettingsRepo):
        self._bot = bot
        self._polls = polls
        self._conf = conf

    async def send_informatics_poll(self, question: str, options: List[str]) -> str:
        chat_id_str = self._conf.get("informatics_chat_id")
        if not chat_id_str:
            raise RuntimeError("Чат информатики не привязан. Используйте /bind_here в нужном чате.")
        chat_id = int(chat_id_str)

        options = _ensure_tyk(options)

        msg = await self._bot.send_poll(
            chat_id=chat_id,
            question=question,
            options=options,
            is_anonymous=False,
            allows_multiple_answers=True,
        )
        poll_id = msg.poll.id if msg.poll else ""
        if not poll_id:
            # fallback: Telegram may not return poll immediately (rare)
            await asyncio.sleep(0.2)
            if msg.poll and msg.poll.id:
                poll_id = msg.poll.id
            else:
                raise RuntimeError("Не удалось получить poll_id от Telegram")

        self._polls.upsert(
            Poll(
                poll_id=poll_id,
                message_id=msg.message_id,
                chat_id=chat_id,
                question=question,
                options=options,
            )
        )
        return poll_id
