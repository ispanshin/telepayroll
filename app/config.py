from __future__ import annotations
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    bot_token: str
    admin_ids: List[int] = []
    data_dir: Path = Path("./data")
    db_path: Path | None = None
    informatics_chat_id: int | None = None  # чат, куда отправляем опросы

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_nested_delimiter=","
    )

    @property
    def database_file(self) -> Path:
        return self.db_path or (self.data_dir / "telepayroll.sqlite3")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return [int(x) for x in v]
        # comma separated string
        return [int(x.strip()) for x in str(v).split(",") if x.strip()]
