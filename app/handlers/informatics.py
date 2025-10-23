from __future__ import annotations
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, PollAnswer
from ..context import AppContext
from ..utils.auth import ensure_admin_message

router = Router()


@router.message(Command("bind_here"), F.chat.type.in_({"group", "supergroup"}))
async def bind_here(msg: Message, ctx: AppContext):
    if not await ensure_admin_message(msg, ctx.settings.admin_ids):
        return
    chat_id = msg.chat.id
    ctx.conf.set("informatics_chat_id", str(chat_id))
    await msg.answer(f"Привязал этот чат для опросов. chat_id={chat_id}")


@router.poll_answer()
async def on_poll_answer(ans: PollAnswer, ctx: AppContext):
    try:
        # сохраняем только если опрос известен нам
        if ctx.polls.get(ans.poll_id) is None:
            return

        uid = int(ans.user.id)
        username = ans.user.username
        first_name = ans.user.first_name
        last_name = ans.user.last_name
        option_ids = sorted(set(int(x) for x in (ans.option_ids or [])))

        ctx.votes.save_answer(
            poll_id=ans.poll_id,
            user_id=uid,
            option_ids=option_ids,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
    except Exception:
        # тут можно залогировать, чтобы не ронять обработку апдейтов
        return
