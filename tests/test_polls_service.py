# tests/test_polls_service.py
import types
import pytest
import asyncio
from app.services.polls import PollsService

class FakePoll:
    def __init__(self, id): self.id = id

class FakeMessage:
    def __init__(self, message_id=10, poll_id="P-123"):
        self.message_id = message_id
        self.poll = FakePoll(poll_id)

class FakeBot:
    def __init__(self):
        self.calls = []
    async def send_poll(self, **kwargs):
        self.calls.append(kwargs)
        return FakeMessage(poll_id="P-OK")

@pytest.mark.asyncio
async def test_send_informatics_poll_ok(repos):
    # настроим чат
    repos.conf.set("informatics_chat_id", "12345")
    bot = FakeBot()
    svc = PollsService(bot=bot, polls=repos.polls, conf=repos.conf)

    poll_id = await svc.send_informatics_poll("Вопрос", ["a","b"])
    assert poll_id == "P-OK"
    # записалось в БД
    saved = repos.polls.get("P-OK")
    assert saved is not None
    assert saved.question == "Вопрос"
    assert saved.options == ["a","b"]
    # и телега вызывалась
    assert bot.calls and bot.calls[0]["chat_id"] == 12345