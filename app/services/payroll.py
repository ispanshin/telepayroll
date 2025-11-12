from __future__ import annotations
from typing import List, Tuple
from ..domain.payroll import PayrollContext, build_payroll_context
from ..infra.repos.teachers import TeachersRepo
from ..infra.repos.votes import VotesRepo


class PayrollService:
    def __init__(self, teachers: TeachersRepo, votes: VotesRepo):
        self._teachers = teachers
        self._votes = votes

    def context(self, poll_id: str) -> PayrollContext:
        teachers = list(self._teachers.list_all())
        roster = [(t.id, t.name, t.service_number, t.default_rate) for t in teachers]
        answers = self._votes.answers_by_poll(poll_id)
        names = {t.id: t.name for t in teachers if t.id in answers}


        return build_payroll_context(
            poll_id=poll_id, roster=roster, answers=answers, voters_names=names
        )
