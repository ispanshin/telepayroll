from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from pathlib import Path



@contextmanager
def connect(db_path: str):
    cn = sqlite3.connect(db_path)
    cn.row_factory = sqlite3.Row
    try:
        cn.execute("PRAGMA journal_mode=WAL;")
        cn.execute("PRAGMA synchronous=NORMAL;")
        cn.execute("PRAGMA foreign_keys=ON;")
        yield cn
        cn.commit()
    finally:
        cn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS polls (
  poll_id TEXT PRIMARY KEY,
  message_id INTEGER NOT NULL,
  chat_id INTEGER NOT NULL,
  question TEXT NOT NULL,
  options_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS votes (
  poll_id TEXT NOT NULL,
  user_id INTEGER NOT NULL,
  option_ids_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (poll_id, user_id),
  FOREIGN KEY (poll_id) REFERENCES polls(poll_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS teachers (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  service_number TEXT NUT NULL,
  default_rate REAL NOT NULL DEFAULT 1.0
);
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_polls_created_at ON polls(created_at);
CREATE INDEX IF NOT EXISTS idx_votes_poll      ON votes(poll_id);
"""


def ensure_schema(db_path: str, connect_fn=connect) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with connect_fn(db_path) as cn:
        cn.executescript(SCHEMA)
