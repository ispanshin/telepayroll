from __future__ import annotations
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest

from ..context import AppContext
from ..utils.callback_data import PayrollAdd
from ..utils.auth import ensure_admin_callback
from ..services.ui import payroll_screen_text_and_kb
from ..infra.repos.teachers import Teacher

from html import escape
from aiogram.filters import Command
from aiogram.types import Message
from ..utils.auth import ensure_admin_message

router = Router()


class AddTeacherSG(StatesGroup):
    waiting_name = State() # сначала имя
    waiting_rate = State() # потом ставка


@router.callback_query(PayrollAdd.filter())
async def cb_add_teacher(
        cb: CallbackQuery, callback_data: PayrollAdd, ctx: AppContext, state: FSMContext
):
    """
    Шаг 1: по нажатию «Добавить …» просим ввести Имя Фамилию,
    подсказываем вариант из ТГ (username/ФИО), но сохраняем ТОЛЬКО своё.
    """
    if not await ensure_admin_callback(cb, ctx.settings.admin_ids):
        return
    await cb.answer()  # сразу гасим «часики»

    uid = int(callback_data.teacher_id)

    # Подсказка для администратора: имя из голосов (может быть @username / ФИО / id)
    suggested_map = ctx.votes.voter_display_names(callback_data.poll_id)
    suggested = (suggested_map.get(uid) or str(uid)).strip()

    # Запоминаем контекст экрана, чтобы потом его обновить
    await state.update_data(
        poll_id=callback_data.poll_id,
        teacher_id=uid,
        screen_chat_id=cb.message.chat.id if cb.message else None,
        screen_message_id=cb.message.message_id if cb.message else None,
        suggested_name=suggested,
    )
    await state.set_state(AddTeacherSG.waiting_name)

    await cb.message.answer(
        "Введи Имя Фамилию для преподавателя.\n"
        f"Подсказка из ТГ: <code>{suggested}</code>\n"
        "Если хочешь оставить подсказку как есть — пришли «-»."
    )


@router.message(AddTeacherSG.waiting_name, F.text)
async def add_teacher_name(msg: Message, state: FSMContext, ctx: AppContext):
    """
    Шаг 2: принимаем ввод, сохраняем в teachers и обновляем экран payroll.
    """
    data = await state.get_data()
    raw = (msg.text or "").strip()
    uid = int(data["teacher_id"])
    poll_id = data["poll_id"]
    suggested = (data.get("suggested_name") or "").strip() or str(uid)

    # Если админ прислал "-" или пусто — берём подсказку как есть
    name = suggested if raw in {"", "-"} else raw
    name = name[:128]  # небольшая санитария по длине

    # Сохраняем «официальное» имя только у себя
    ctx.teachers.upsert(Teacher(id=uid, name=name, default_rate=1.0))

    # Обновляем экран payroll (если знаем, какое сообщение править)
    chat_id = data.get("screen_chat_id")
    message_id = data.get("screen_message_id")
    if chat_id and message_id:
        pc = ctx.payroll_service.context(poll_id)
        text, kb = payroll_screen_text_and_kb(pc, include_missing_zero=False)
        try:
            await ctx.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=kb,
            )
        except TelegramBadRequest as e:
            # Игнор, если контент не поменялся
            if "message is not modified" not in str(e):
                raise

    await msg.answer(f"Добавил в ростер: {name}")
    await state.clear()


@router.message(Command(commands=["roster", "teachers"]))
async def show_roster(msg: Message, ctx: AppContext):
    # только для админов
    if not await ensure_admin_message(msg, ctx.settings.admin_ids):
        return

    teachers = ctx.teachers.list_all()
    if not teachers:
        await msg.answer("Ростер пуст.")
        return

    # сортируем по имени, экранируем HTML
    teachers.sort(key=lambda t: (t.name.casefold(), t.id))

    lines = ["<b>Ростер преподавателей</b>", ""]
    for t in teachers:
        lines.append(f"• {escape(t.name)} — rate: <b>{t.default_rate:g}</b> (id={t.id})")

    text = "\n".join(lines)

    # телега ограничивает длину сообщения ~4096 символами — разрежем при необходимости
    chunks = []
    cur = []
    size = 0
    for line in lines:
        if size + len(line) + 1 > 4000:
            chunks.append("\n".join(cur))
            cur, size = [], 0
        cur.append(line)
        size += len(line) + 1
    if cur:
        chunks.append("\n".join(cur))

    for i, chunk in enumerate(chunks, 1):
        suffix = f"\n\nСтраница {i}/{len(chunks)}" if len(chunks) > 1 else ""
        await msg.answer(chunk + suffix)


@router.message(AddTeacherSG.waiting_name)
async def add_teacher_name_not_text(msg: Message):
    await msg.answer(
        "Нужен текст. Пришли Имя Фамилию сообщением или «-», чтобы оставить подсказку."
    )


@router.message(Command(commands=["remove_teacher", "del_teacher"]))
async def cmd_remove_teacher(msg: Message, ctx: AppContext):
    # только админ
    if not await ensure_admin_message(msg, ctx.settings.admin_ids):
        return

    text = (msg.text or "").strip()
    parts = text.split(maxsplit=1)  # ['/remove_teacher', 'Имя Фамилия ...']
    if len(parts) < 2:
        await msg.answer("Формат: /remove_teacher <Имя Фамилия...>")
        return

    name = parts[1].strip()
    if not name:
        await msg.answer("Имя не может быть пустым.")
        return

    deleted = ctx.teachers.delete_by_name(name)
    if deleted == 0:
        await msg.answer(f"Не нашёл в ростере: <b>{escape(name)}</b>")
        return

    await msg.answer(f"Удалил из ростера: <b>{escape(name)}</b> (записей: {deleted})")
