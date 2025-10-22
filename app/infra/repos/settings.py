from __future__ import annotations

class SettingsRepo:
    def __init__(self, db_path: str, connect):
        self._db_path = db_path
        self._connect = connect

    def get(self, key: str) -> str | None:
        with self._connect(self._db_path) as cn:
            row = cn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            return row["value"] if row else None

    def set(self, key: str, value: str) -> None:
        with self._connect(self._db_path) as cn:
            cn.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )
