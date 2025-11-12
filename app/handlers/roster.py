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
    waiting_service_number = State() # потом табельный номер


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
    suggested = str(uid)

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
        "Введи ФИО для преподавателя.\n"
        f"Подсказка из ТГ: <code>{suggested}</code>\n"
    )


@router.message(AddTeacherSG.waiting_name, F.text)
async def add_teacher_name(msg: Message, state: FSMContext, ctx: AppContext):
    """Шаг 1: принимаем имя, просим ставку."""
    data = await state.get_data()
    raw = (msg.text or "").strip()
    uid = int(data["teacher_id"])
    suggested = (data.get("suggested_name") or "").strip() or str(uid)

    name = suggested if raw in {"", "-"} else raw
    name = name[:128]
    if not name:
        await msg.answer("Имя не может быть пустым. Пришли ФИО или «-».")
        return

    await state.update_data(final_name=name)
    await state.set_state(AddTeacherSG.waiting_rate)

    await msg.answer(
        f"Ок, имя: <b>{escape(name)}</b>.\n"
        "Теперь введи <b>ставку</b> (например: 1, 2500 или 0.5). "
        "Если оставить по умолчанию — пришли «-».",
    )


def _parse_rate(text: str) -> float | None:
    t = (text or "").strip()
    if t in {"", "-"}:
        return 1.0
    t = t.replace(",", ".")
    try:
        rate = float(t)
    except ValueError:
        return None
    # можно добавить свои ограничения:
    if rate <= 0:
        return None
    return rate


@router.message(AddTeacherSG.waiting_rate, F.text)
async def add_teacher_rate(msg: Message, state: FSMContext, ctx: AppContext):
    """Шаг 2: принимаем ставку, сохраняем teacher, обновляем экран."""
    data = await state.get_data()
    uid = int(data["teacher_id"])
    name = data.get("final_name") or (data.get("suggested_name") or str(uid))

    rate = _parse_rate(msg.text or "")
    if rate is None:
        await msg.answer("Не понял ставку. Пришли число (например 1, 2500 или 228), либо «-» для 1.")
        return

    await state.update_data(rate=rate)
    await state.set_state(AddTeacherSG.waiting_service_number)

    await msg.answer(
        "Отлично.\n"
        f"Теперь введи <b>табельный номер</b> для преподавателя <b>{escape(name)}</b>.\n"
        "Это обязательное поле (пришли любой непустой текст, например: 42 или M-23)."
    )


@router.message(AddTeacherSG.waiting_service_number, F.text)
async def add_teacher_service_number(msg: Message, state: FSMContext, ctx: AppContext):
    data = await state.get_data()
    uid = int(data["teacher_id"])
    poll_id = data["poll_id"]
    name = data.get("final_name") or (data.get("suggested_name") or str(uid))
    rate = float(data["rate"])

    service_number = (msg.text or "").strip()
    if not service_number:
        await msg.answer("табельный номер не может быть пустым. Пришли хоть что-то.")
        return

    ctx.teachers.upsert(
        Teacher(
            id=uid,
            name=name,
            default_rate=rate,
            service_number=service_number,
        )
    )

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
            if "message is not modified" not in str(e):
                raise

    await msg.answer(
        f"Добавил: <b>{escape(name)}</b> со ставкой <b>{rate:g}</b>, "
        f"табельный номер: <b>{escape(service_number)}</b>."
    )
    await state.clear()


@router.message(Command(commands=["roster", "teachers"]))
async def show_roster(msg: Message, ctx: AppContext):
    if not await ensure_admin_message(msg, ctx.settings.admin_ids):
        return

    teachers = ctx.teachers.list_all()
    if not teachers:
        await msg.answer("Ростер пуст.")
        return


    lines = ["<b>Ростер преподавателей</b>", ""]
    for t in teachers:
        sn = t.service_number
        lines.append(
            f"• {escape(t.name)} — rate: <b>{t.default_rate:g}</b>, "
            f"service: <b>{escape(sn)}</b> (id={t.id})"
        )

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
    parts = text.split(maxsplit=1)  # ['/remove_teacher', 'ФИО ...']
    if len(parts) < 2:
        await msg.answer("Формат: /remove_teacher <ФИО...>")
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
