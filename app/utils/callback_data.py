from __future__ import annotations
from aiogram.filters.callback_data import CallbackData


class PayrollOpen(CallbackData, prefix="payroll_open"):
    poll_id: str


class PayrollAdd(CallbackData, prefix="payroll_add"):
    poll_id: str
    teacher_id: int
