from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
import json

@dataclass
class Poll:
    poll_id: str
    message_id: int
    chat_id: int
    question: str
    options: list[str]

class PollsRepo:
    def __init__(self, db_path: str, connect):
        self._db_path = db_path
        self._connect = connect

    def upsert(self, p: Poll) -> None:
        with self._connect(self._db_path) as cn:
            cn.execute(
                """
                INSERT OR REPLACE INTO polls(poll_id, message_id, chat_id, question, options_json, created_at)
                VALUES (?,?,?,?,?,datetime('now'))
                """,
                (p.poll_id, p.message_id, p.chat_id, p.question, json.dumps(p.options, ensure_ascii=False)),
            )

    def get(self, poll_id: str) -> Optional[Poll]:
        with self._connect(self._db_path) as cn:
            row = cn.execute("SELECT * FROM polls WHERE poll_id=?", (poll_id,)).fetchone()
            if not row:
                return None
            return Poll(
                poll_id=row["poll_id"],
                message_id=row["message_id"],
                chat_id=row["chat_id"],
                question=row["question"],
                options=json.loads(row["options_json"]) or [],
            )

    def get_last(self) -> Optional[Poll]:
        with self._connect(self._db_path) as cn:
            row = cn.execute("SELECT * FROM polls ORDER BY created_at DESC LIMIT 1").fetchone()
            if not row:
                return None
            return Poll(
                poll_id=row["poll_id"],
                message_id=row["message_id"],
                chat_id=row["chat_id"],
                question=row["question"],
                options=json.loads(row["options_json"]) or [],
            )
