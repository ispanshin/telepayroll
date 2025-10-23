from __future__ import annotations

import asyncio
from typing import List
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from ..infra.repos.polls import PollsRepo, Poll
from ..infra.repos.settings import SettingsRepo
from typing import List, Iterable


def _ensure_tyk(options: Iterable[str],
                tyk_text: str = 'Тык',
                enforce_limit: bool = True) -> List[str]:
    """
    Возвращает список опций, где ровно один 'Тык' стоит последним.
    Удаляем все варианты 'Тык' (без учёта регистра/пробелов),
    чистим пустые строки.
    """
    MAX_POLL_OPTIONS = 10
    norm_tyk = tyk_text.strip().casefold()

    cleaned: List[str] = []
    for o in options:
        s = (o or "").strip()
        if not s:
            continue
        if s.casefold() == norm_tyk:
            continue  # выбрасываем все встретившиеся 'Тык'
        cleaned.append(s)

    # добавляем единственный 'Тык' в конец
    cleaned.append(tyk_text.strip())

    if enforce_limit and len(cleaned) > MAX_POLL_OPTIONS:
        # оставляем первые n-1 обычных + 'Тык'
        cleaned = cleaned[:MAX_POLL_OPTIONS - 1] + [tyk_text.strip()]

    return cleaned

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
