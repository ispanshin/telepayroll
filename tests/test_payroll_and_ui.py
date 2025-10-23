# tests/test_payroll_and_ui.py
from app.services.payroll import PayrollService
from app.services.ui import payroll_screen_text_and_kb
from app.infra.repos.teachers import Teacher

def test_payroll_context_and_ui(repos):
    # roster
    repos.teachers.upsert(Teacher(id=1, name="Alice <&>", default_rate=2))
    repos.teachers.upsert(Teacher(id=2, name="Bob", default_rate=1))
    # answers: Alice = 3 класса, а некто 999 — аутсайдер
    repos.votes.save_answer("P", 1, [0,1,2], username=None, first_name="A", last_name=None)
    repos.votes.save_answer("P", 999, [0], username="outsider", first_name="X", last_name="Y")

    svc = PayrollService(teachers=repos.teachers, votes=repos.votes)
    ctx = svc.context("P")

    # проверяем расчёты
    rows = {r.teacher_id: r for r in ctx.per_teacher}
    assert rows[1].classes == 3 and rows[1].amount == 3*2
    assert rows[2].classes == 0
    assert any(uid == 999 for uid, _ in ctx.outsiders)
    # UI: HTML экранирован и есть кнопка добавления
    text, kb = payroll_screen_text_and_kb(ctx)
    assert "&lt;&amp;&gt;" in text  # Alice <&> экранирована
    # кнопки: хотя бы одна "Добавить ..."
    assert kb.inline_keyboard and kb.inline_keyboard[0][0].text.startswith("Добавить")