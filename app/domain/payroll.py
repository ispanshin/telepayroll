from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Iterable, Tuple


@dataclass
class PayrollRow:
    teacher_id: int
    teacher_name: str
    service_number: str
    classes: int
    rate: float
    amount: float


@dataclass
class PayrollContext:
    poll_id: str
    per_teacher: List[PayrollRow]
    missing_ids: List[int]
    outsiders: List[Tuple[int, str]]
    total_amount: float


def build_payroll_context(
    *,
    poll_id: str,
    roster: Iterable[Tuple[int, str, str, float]],
    answers: Dict[int, List[int]],
    voters_names: Dict[int, str],
) -> PayrollContext:
    # roster: (id, name, rate)
    roster_map = {int(tid): (name, service_number, float(rate)) for tid, name, service_number, rate in roster}
    per_teacher: List[PayrollRow] = []
    missing_ids: List[int] = []

    # For each teacher in roster, compute classes from answers
    for tid, (name, service_number, rate) in roster_map.items():

        votes = answers.get(tid, [])
        classes = len(votes)

        if classes == 0:
            missing_ids.append(tid)

        if -1 in votes:
            classes -= 1
            # не считаем тык

        per_teacher.append(
            PayrollRow(
                teacher_id=tid, teacher_name=name, service_number=service_number, classes=classes, rate=rate, amount=classes * rate
            )
        )

    # outsiders: answered but not in roster
    outsiders_ids = [uid for uid in answers.keys() if uid not in roster_map]
    outsiders = [(uid, voters_names.get(uid, str(uid))) for uid in outsiders_ids]
    total_amount = sum(r.amount for r in per_teacher)
    per_teacher.sort(key=lambda r: (r.teacher_name.casefold(), r.teacher_id))
    return PayrollContext(
        poll_id=poll_id,
        per_teacher=per_teacher,
        missing_ids=missing_ids,
        outsiders=outsiders,
        total_amount=total_amount,
    )
