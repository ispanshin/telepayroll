from __future__ import annotations
from html import escape
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ..domain.payroll import PayrollContext
from ..utils.callback_data import PayrollAdd

MAX_MISSING_SHOW = 20  # сколько имен показывать максимум в списке

def _short(s: str, n: int) -> str:
    s = s.strip()
    return s if len(s) <= n else s[: max(0, n - 1)] + "…"


def _profile_url(uid: int, username: str | None) -> str:
    # если знаем username — ведём на https://t.me/username, иначе — tg://user?id=...
    return f"https://t.me/{username}" if username else f"tg://user?id={uid}"


def _profile_link_html(uid: int, username: str | None, label: str | None = None) -> str:
    url = _profile_url(uid, username)
    text = label if label else (f"@{username}" if username else str(uid))
    return f'<a href="{escape(url)}">{escape(text)}</a>'


def payroll_screen_text_and_kb(ctx: PayrollContext, *, include_missing_zero: bool = False):
    lines = ["<b>Итоги (payroll)</b>", ""]

    # Табличка по преподам
    for row in ctx.per_teacher:
        if not include_missing_zero and row.classes == 0:
            continue
        mark = "✅" if row.classes > 0 else "—"
        teacher = escape(str(row.teacher_name))
        lines.append(f"{mark} {teacher}: {row.classes} × {row.rate:g} = <b>{row.amount:g}</b>")

    lines.append("")
    lines.append(f"Итого: <b>{ctx.total_amount:g}</b>")

    usernames = getattr(ctx, "usernames", {}) or {}

    # 👉 БЛОК: Преподаватели, которые не голосовали
    missing_rows = [r for r in ctx.per_teacher if r.classes == 0]
    if missing_rows:
        lines.append("")
        lines.append(f"<b>Не голосовали ({len(missing_rows)}):</b>")
        for r in missing_rows[:MAX_MISSING_SHOW]:
            uname = usernames.get(r.teacher_id)  # может быть None — тогда уйдём по tg://id
            link = _profile_link_html(r.teacher_id, uname, str(r.teacher_name))
            lines.append(f" • {link}")
        if len(missing_rows) > MAX_MISSING_SHOW:
            lines.append(f"… и ещё {len(missing_rows) - MAX_MISSING_SHOW}")

    # Список аутсайдеров (голосовали, но не в ростере)
    if ctx.outsiders:
        lines.append("")
        lines.append("<b>Новые голосовавшие (не в ростере):</b>")
        # если в контексте есть usernames — используем, иначе None
        for uid, name in ctx.outsiders[:10]:
            link = _profile_link_html(uid, usernames.get(uid))
            lines.append(f" • {escape(str(name))} — {link}")

    text = "\n".join(lines)

    # Кнопки
    kb = InlineKeyboardBuilder()
    usernames = getattr(ctx, "usernames", {}) or {}
    for uid, name in ctx.outsiders[:10]:
        # кнопка "Добавить ..."
        kb.button(
            text=_short(f"Добавить {name}", 64),
            callback_data=PayrollAdd(poll_id=ctx.poll_id, teacher_id=uid).pack(),
        )
        # кнопка "Профиль"
        kb.button(
            text="Профиль",
            url=_profile_url(uid, usernames.get(uid)),
        )
    kb.adjust(2)  # по два в ряд: [Добавить][Профиль]

    return text, kb.as_markup()
