# tests/test_roster_flow.py
import pytest
from types import SimpleNamespace
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from app.handlers.roster import router, AddTeacherSG, cb_add_teacher, add_teacher_name
from app.utils.callback_data import PayrollAdd
from app.infra.repos.polls import Poll
from app.infra.repos.teachers import Teacher


class FakeMessage:
    def __init__(self):
        self.chat = SimpleNamespace(id=777)
        self.message_id = 100
        self._answers = []

    async def answer(self, text, reply_markup=None):
        self._answers.append(text)


class FakeCallback:
    def __init__(self):
        self.from_user = SimpleNamespace(id=1)
        self.message = FakeMessage()

    async def answer(self, *a, **kw):
        pass


class FakeBot:
    async def edit_message_text(self, **kwargs):
        return None


@pytest.mark.asyncio
async def test_add_teacher_flow(repos):
    repos.polls.upsert(
        Poll(
            poll_id="P",
            message_id=0,
            chat_id=0,
            question="q",
            options=["x", "y"],
        )
    )

    # подготовка контекста
    ctx = SimpleNamespace(
        settings=SimpleNamespace(admin_ids=[1]),
        votes=repos.votes,
        teachers=repos.teachers,
        polls=repos.polls,
        conf=repos.conf,
        bot=FakeBot(),
        payroll_service=SimpleNamespace(
            context=lambda poll_id: SimpleNamespace(
                poll_id=poll_id, per_teacher=[], missing_ids=[], outsiders=[], total_amount=0
            )
        ),
    )
    repos.votes.save_answer("P", 123, [0], username="user", first_name="Ivan", last_name="Petrov")

    storage = MemoryStorage()
    # эмулируем callback «Добавить 123»
    cb = FakeCallback()
    cd = PayrollAdd(poll_id="P", teacher_id=123)

    state = FSMContext(storage, key=("bot", 777, 1))  # (bot_id, chat_id, user_id)
    await cb_add_teacher(cb=cb, callback_data=cd, ctx=ctx, state=state)

    # второй шаг — отправляем имя
    msg = FakeMessage()
    msg.from_user = SimpleNamespace(id=1)
    msg.text = "Петров Иван"
    await add_teacher_name(msg=msg, state=state, ctx=ctx)

    t = repos.teachers.get(123)
    assert t and t.name == "Петров Иван"
