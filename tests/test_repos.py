# tests/test_repos.py
from app.infra.repos.polls import Poll
import json

def test_polls_upsert_get(repos):
    p = Poll(poll_id="p1", message_id=1, chat_id=42, question="Q", options=["a","b"])
    repos.polls.upsert(p)
    got = repos.polls.get("p1")
    assert got is not None
    assert got.poll_id == "p1"
    assert got.options == ["a","b"]

def test_votes_save_and_read(repos):
    repos.votes.save_answer("p1", 100, [1,2,2], username="u", first_name="Ivan", last_name="Petrov")
    ans = repos.votes.answers_by_poll("p1")
    assert ans[100] == [1,2,2] or ans[100] == [1,2]  # зависит от твоей нормализации
    names = repos.votes.voter_display_names("p1")
    assert names[100] in {"@u", "Ivan Petrov"}

def test_teachers_upsert_list_get(repos):
    from app.infra.repos.teachers import Teacher
    repos.teachers.upsert(Teacher(id=1, name="Alice", default_rate=1))
    repos.teachers.upsert(Teacher(id=2, name="Bob", default_rate=2))
    all_ = repos.teachers.list_all()
    assert {t.name for t in all_} == {"Alice", "Bob"}
    t = repos.teachers.get(1)
    assert t.name == "Alice"