from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple


@dataclass
class Teacher:
    id: int
    name: str
    default_rate: float


class TeachersRepo:
    def __init__(self, db_path: str, connect):
        self._db_path = db_path
        self._connect = connect

    def delete_by_name(self, name: str) -> int:
        name = (name or "").strip()
        if not name:
            return 0
        with self._connect(self._db_path) as cn:
            cur = cn.execute("DELETE FROM teachers WHERE name = ?", (name,))
            return cur.rowcount  # сколько строк удалили

    def delete_by_id(self, teacher_id: int) -> int:
        with self._connect(self._db_path) as cn:
            cur = cn.execute("DELETE FROM teachers WHERE id = ?", (int(teacher_id),))
            return cur.rowcount

    def upsert(self, teacher: Teacher) -> None:
        with self._connect(self._db_path) as cn:
            cn.execute(
                """
                INSERT INTO teachers(id, name, default_rate)
                VALUES(?,?,?)
                ON CONFLICT(id) DO UPDATE SET name=excluded.name, default_rate=excluded.default_rate
                """,
                (teacher.id, teacher.name, teacher.default_rate),
            )

    def get(self, teacher_id: int) -> Optional[Teacher]:
        with self._connect(self._db_path) as cn:
            row = cn.execute(
                "SELECT id, name, default_rate FROM teachers WHERE id=?", (teacher_id,)
            ).fetchone()
            if not row:
                return None
            return Teacher(
                id=int(row["id"]), name=row["name"], default_rate=float(row["default_rate"])
            )

    def list_all(self) -> List[Teacher]:
        with self._connect(self._db_path) as cn:
            return [
                Teacher(id=int(r["id"]), name=r["name"], default_rate=float(r["default_rate"]))
                for r in cn.execute(
                    "SELECT id, name, default_rate FROM teachers ORDER BY name"
                ).fetchall()
            ]

    def list_by_ids(self, ids: Iterable[int]) -> List[Teacher]:
        ids = list(ids)
        if not ids:
            return []
        placeholders = ",".join(["?"] * len(ids))
        with self._connect(self._db_path) as cn:
            rows = cn.execute(
                f"SELECT id, name, default_rate FROM teachers WHERE id IN ({placeholders})",
                tuple(ids),
            ).fetchall()
            return [
                Teacher(id=int(r["id"]), name=r["name"], default_rate=float(r["default_rate"]))
                for r in rows
            ]
