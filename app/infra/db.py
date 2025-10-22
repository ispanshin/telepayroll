from __future__ import annotations
import sqlite3
from contextlib import contextmanager

@contextmanager
def connect(db_path: str):
    cn = sqlite3.connect(db_path)
    cn.row_factory = sqlite3.Row
    try:
        cn.execute("PRAGMA journal_mode=WAL;")
        cn.execute("PRAGMA synchronous=NORMAL;")
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
  options_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS votes (
  poll_id TEXT NOT NULL,
  user_id INTEGER NOT NULL,
  option_ids_json TEXT NOT NULL,
  username TEXT,
  first_name TEXT,
  last_name TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (poll_id, user_id)
);
CREATE TABLE IF NOT EXISTS teachers (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  default_rate REAL NOT NULL DEFAULT 1.0
);
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
"""

def ensure_schema(db_path: str, connect_fn=connect) -> None:
    with connect_fn(db_path) as cn:
        cn.executescript(SCHEMA)
