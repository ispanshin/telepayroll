from __future__ import annotations
from aiogram.types import Message, CallbackQuery


def is_admin(user_id: int, admin_ids: list[int]) -> bool:
    return int(user_id) in set(int(x) for x in admin_ids)


async def ensure_admin_message(msg: Message, admin_ids: list[int]) -> bool:
    if not is_admin(msg.from_user.id, admin_ids):
        await msg.answer("Команда доступна только администраторам.")
        return False
    return True


async def ensure_admin_callback(cb: CallbackQuery, admin_ids: list[int]) -> bool:
    if not cb.from_user or not is_admin(cb.from_user.id, admin_ids):
        await cb.answer("Недостаточно прав.", show_alert=True)
        return False
    return True
