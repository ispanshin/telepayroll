# tests/test_admin_mw.py
import asyncio
import types
import pytest
from app.middlewares.admin_only import AdminOnlyMiddleware


class DummyUser:
    def __init__(self, id):
        self.id = id


class DummyMessage:
    def __init__(self, uid):
        self.from_user = DummyUser(uid)


@pytest.mark.asyncio
async def test_admin_only_blocks_non_admin():
    mw = AdminOnlyMiddleware(admin_ids=[1, 2, 3])
    called = False

    async def handler(ev, data):
        nonlocal called
        called = True

    await mw(handler, DummyMessage(uid=999), {})
    assert called is False


@pytest.mark.asyncio
async def test_admin_only_allows_admin():
    mw = AdminOnlyMiddleware(admin_ids=[1, 2, 3])
    called = False

    async def handler(ev, data):
        nonlocal called
        called = True

    await mw(handler, DummyMessage(uid=2), {})
    assert called is True
