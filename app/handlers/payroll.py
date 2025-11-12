from __future__ import annotations
import csv
import io

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from ..context import AppContext
from ..services.ui import payroll_screen_text_and_kb
from ..utils.callback_data import PayrollOpen, PayrollAdd
from ..utils.auth import ensure_admin_message, ensure_admin_callback

router = Router()


@router.message(Command("payroll_csv"))
async def payroll_csv(msg: Message, ctx: AppContext):
    if not await ensure_admin_message(msg, ctx.settings.admin_ids):
        return

    last = ctx.polls.get_last()
    if not last:
        await msg.answer("Пока нет ни одного опроса.")
        return

    # считаем контекст по последнему опросу
    pc = ctx.payroll_service.context(last.poll_id)


    # готовим CSV в памяти
    buf = io.StringIO()
    writer = csv.writer(buf)

    # заголовки колонок для Google Sheets
    writer.writerow(["ФИО", "ВЫПЛАТА", "ТАБЕЛЬНЫЙ НОМЕР"])

    for row in pc.per_teacher:
        sn = row.service_number
        writer.writerow([row.teacher_name, f"{row.amount:.2f}", sn])

    data = buf.getvalue().encode("utf-8-sig")
    filename = f"payroll_{last.poll_id}.csv"

    file = BufferedInputFile(data, filename=filename)
    await msg.answer_document(file, caption="CSV для импорта в Google Sheets")


@router.message(Command("payroll"))
async def open_latest_payroll(msg: Message, ctx: AppContext):
    if not await ensure_admin_message(msg, ctx.settings.admin_ids):
        return
    last = ctx.polls.get_last()
    if not last:
        await msg.answer("Пока нет ни одного опроса.")
        return
    pc = ctx.payroll_service.context(last.poll_id)
    text, kb = payroll_screen_text_and_kb(pc, include_missing_zero=False)
    await msg.answer(text, reply_markup=kb)
