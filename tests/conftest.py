# tests/conftest.py
from __future__ import annotations
import os, sqlite3, types
import pytest
import asyncio
from contextlib import contextmanager
from app.infra.db import ensure_schema  # поправь импорт под свой пакет
from app.infra.repos.polls import PollsRepo, Poll
from app.infra.repos.votes import VotesRepo
from app.infra.repos.teachers import TeachersRepo
from app.infra.repos.settings import SettingsRepo

@contextmanager
def test_connect(db_path: str):
    cn = sqlite3.connect(db_path)
    cn.row_factory = sqlite3.Row
    cn.execute("PRAGMA foreign_keys=ON;")
    cn.execute("PRAGMA journal_mode=WAL;")
    cn.execute("PRAGMA synchronous=NORMAL;")
    try:
        yield cn
        cn.commit()
    finally:
        cn.close()

@pytest.fixture()
def db_path(tmp_path):
    p = tmp_path / "test.sqlite3"
    ensure_schema(str(p), connect_fn=test_connect)
    return str(p)

@pytest.fixture()
def repos(db_path):
    return types.SimpleNamespace(
        polls=PollsRepo(db_path, test_connect),
        votes=VotesRepo(db_path, test_connect),
        teachers=TeachersRepo(db_path, test_connect),
        conf=SettingsRepo(db_path, test_connect),
    )