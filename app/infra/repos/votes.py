from __future__ import annotations
from typing import Dict, List
import json


class VotesRepo:
    def __init__(self, db_path: str, connect):
        self._db_path = db_path
        self._connect = connect

    def save_answer(
        self,
        poll_id: str,
        user_id: int,
        option_ids: List[int],
    ) -> None:
        with self._connect(self._db_path) as cn:
            if not option_ids:
                # если все варианты сняли — считаем, что голоса нет
                cn.execute("DELETE FROM votes WHERE poll_id=? AND user_id=?", (poll_id, user_id))
                return

            cn.execute(
                """
                INSERT OR REPLACE INTO votes(poll_id, user_id, option_ids_json, created_at)
                VALUES (?,?,?,datetime('now'))
                """,
                (poll_id, user_id, json.dumps(option_ids)),
            )

    def answers_by_poll(self, poll_id: str) -> Dict[int, List[int]]:
        with self._connect(self._db_path) as cn:
            rows = cn.execute(
                "SELECT user_id, option_ids_json FROM votes WHERE poll_id=?", (poll_id,)
            ).fetchall()
            return {int(r["user_id"]): (json.loads(r["option_ids_json"]) or []) for r in rows}
