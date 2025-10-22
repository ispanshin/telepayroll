from __future__ import annotations
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ..domain.payroll import PayrollContext
from ..utils.callback_data import PayrollOpen, PayrollAdd

def payroll_screen_text_and_kb(ctx: PayrollContext, *, include_missing_zero: bool = False):
    lines = ["<b>Итоги (payroll)</b>", ""]
    for row in ctx.per_teacher:
        if not include_missing_zero and row.classes == 0:
            continue
        mark = "✅" if row.classes > 0 else "—"
        lines.append(f"{mark} {row.teacher_name}: {row.classes} × {row.rate:g} = <b>{row.amount:g}</b>")
    lines.append("")
    lines.append(f"Итого: <b>{ctx.total_amount:g}</b>")
    if ctx.outsiders:
        lines.append("")
        lines.append("<b>Новые голосовавшие (не в ростере):</b>")
        for uid, name in ctx.outsiders[:10]:
            lines.append(f" • {name} (id={uid})")
    text = "\n".join(lines)

    kb = InlineKeyboardBuilder()
    # Кнопки добавления в ростер для первых 10 аутсайдеров
    for uid, name in ctx.outsiders[:10]:
        kb.button(text=f"Добавить {name}", callback_data=PayrollAdd(poll_id=ctx.poll_id, teacher_id=uid).pack())
    kb.adjust(1)
    return text, kb.as_markup()
