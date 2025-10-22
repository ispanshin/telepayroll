from __future__ import annotations
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from ..context import AppContext
from ..utils.text import normalize_options
from ..utils.auth import ensure_admin_message

router = Router()

class NewPollSG(StatesGroup):
    waiting_question = State()
    waiting_options = State()

@router.message(Command("start"))
async def cmd_start(msg: Message):
    await msg.answer("Привет! Я помогу с опросами и подсчётом выплат. Команды: /newpoll, /bind_here (в чате), /payroll")

@router.message(Command("newpoll"))
async def newpoll_start(msg: Message, state: FSMContext, ctx: AppContext):
    if not await ensure_admin_message(msg, ctx.settings.admin_ids):
        return
    await state.set_state(NewPollSG.waiting_question)
    await msg.answer("Введите текст вопроса для опроса:")

@router.message(NewPollSG.waiting_question)
async def newpoll_question(msg: Message, state: FSMContext):
    await state.update_data(question=(msg.text or "").strip())
    await state.set_state(NewPollSG.waiting_options)
    await msg.answer("Введите варианты (через запятую или с новой строки):")

@router.message(NewPollSG.waiting_options)
async def newpoll_options(msg: Message, state: FSMContext, ctx: AppContext):
    options = normalize_options(msg.text or "")
    data = await state.get_data()
    question = data.get("question") or "Опрос"
    poll_id = await ctx.polls_service.send_informatics_poll(question, options)
    await state.clear()
    await msg.answer(f"Опрос отправлен. poll_id=<code>{poll_id}</code>")
