from __future__ import annotations
from typing import Dict, List, Tuple, Iterable
import json

class VotesRepo:
    def __init__(self, db_path: str, connect):
        self._db_path = db_path
        self._connect = connect

    def save_answer(self, poll_id: str, user_id: int, option_ids: List[int],
                    username: str|None, first_name: str|None, last_name: str|None) -> None:
        with self._connect(self._db_path) as cn:
            cn.execute(
                """
                INSERT OR REPLACE INTO votes(poll_id, user_id, option_ids_json, username, first_name, last_name, created_at)
                VALUES (?,?,?,?,?,?,datetime('now'))
                """,
                (poll_id, user_id, json.dumps(option_ids), username, first_name, last_name),
            )

    def answers_by_poll(self, poll_id: str) -> Dict[int, List[int]]:
        with self._connect(self._db_path) as cn:
            rows = cn.execute("SELECT user_id, option_ids_json FROM votes WHERE poll_id=?", (poll_id,)).fetchall()
            return {int(r["user_id"]): (json.loads(r["option_ids_json"]) or []) for r in rows}

    def voter_display_names(self, poll_id: str) -> Dict[int, str]:
        with self._connect(self._db_path) as cn:
            rows = cn.execute(
                "SELECT user_id, username, first_name, last_name FROM votes WHERE poll_id=?", (poll_id,)
            ).fetchall()
            res: Dict[int, str] = {}
            for r in rows:
                uid = int(r["user_id"])
                uname = r["username"]
                fn = r["first_name"] or ""
                ln = r["last_name"] or ""
                if uname:
                    res[uid] = f"@{uname}"
                else:
                    res[uid] = (fn + " " + ln).strip() or str(uid)
            return res
