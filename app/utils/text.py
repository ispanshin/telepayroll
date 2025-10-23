from __future__ import annotations
from typing import Iterable, Sequence
from app.context import AppContext


def normalize_options(raw: str) -> list[str]:
    items = [s.strip() for s in raw.replace("\n", ",").split(",")]
    return [x for x in items if x]
