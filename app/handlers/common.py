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
    await msg.answer(
        "Привет! Я помогу с опросами и подсчётом выплат. Команды: /newpoll, /bind_here (в чате), /payroll"
    )


@router.message(Command("help"))
async def cmd_help(msg: Message):
    text = (
        "<b>Команды</b>\n\n"
        "<b>Общее</b>\n"
        "• /start — приветствие и краткое описание\n"
        "• /help — эта справка\n\n"
        "<b>Админ</b>\n"
        "• /bind_here — привязать <i>текущий групповой чат</i> для опросов\n"
        "• /newpoll — создать опрос (мастер из 2 шагов)\n"
        "• /cancel — отменить текущий мастер\n"
        "• /payroll — показать итоги по последнему опросу\n"
        "• /roster — показать ростер преподавателей (имя и rate)\n"
        "• /teachers — то же, что /roster (алиас)\n"
        "• /remove_teacher &lt;Имя Фамилия...&gt; — удалить преподавателя из ростера по сохранённому имени\n"
    )
    await msg.answer(text)


@router.message(Command("cancel"))
async def cancel(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Окей, отменил.")


@router.message(Command("newpoll"))
async def newpoll_start(msg: Message, state: FSMContext, ctx: AppContext):
    if not await ensure_admin_message(msg, ctx.settings.admin_ids):
        return
    await state.set_state(NewPollSG.waiting_question)
    await msg.answer("Введите текст вопроса для опроса:")


@router.message(NewPollSG.waiting_question, F.text)
async def newpoll_question(msg: Message, state: FSMContext):
    question = (msg.text or "").strip()
    if not question:
        await msg.answer("Нужен непустой текст вопроса. Пришли текст сообщением.")
        return
    await state.update_data(question=question)
    await state.set_state(NewPollSG.waiting_options)
    await msg.answer("Введите варианты (через запятую или с новой строки):")


@router.message(NewPollSG.waiting_options, F.text)
async def newpoll_options(msg: Message, state: FSMContext, ctx: AppContext):
    # нормализация (убрать пустые/дубли, обрезать длину, если нужно)
    options = normalize_options(msg.text or "")
    # базовая валидация количества
    if len(options) < 1:
        await msg.answer("Нужен минимум 1 вариант. Добавь ещё.")
        return
    if len(options) > 9:
        await msg.answer("Слишком много вариантов (максимум 9). Укороти список.")
        return

    data = await state.get_data()
    question = data.get("question") or "Опрос"
    try:
        poll_id = await ctx.polls_service.send_informatics_poll(question, options)
    except Exception as e:
        await state.clear()  # чистим при неудаче, чтобы не зависать в мастере
        await msg.answer(f"Не смог отправить опрос: {e}")
        return

    await state.clear()  # чистим при успехе
    await msg.answer(f"Опрос отправлен. poll_id=<code>{poll_id}</code>")


@router.message(NewPollSG.waiting_question)
async def not_text_question(msg: Message):
    await msg.answer("Нужен текст вопроса. Пришли текст сообщением.")


@router.message(NewPollSG.waiting_options)
async def not_text_options(msg: Message):
    await msg.answer("Нужен список вариантов текстом. Пришли сообщения с вариантами.")
