from __future__ import annotations
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from ..context import AppContext
from ..services.ui import payroll_screen_text_and_kb
from ..utils.callback_data import PayrollOpen, PayrollAdd
from ..utils.auth import ensure_admin_message, ensure_admin_callback

router = Router()


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
