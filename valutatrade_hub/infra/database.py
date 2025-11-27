from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

from ..core.models import User, Portfolio
from .settings import get_settings


class DatabaseManager:
    _instance: "DatabaseManager | None" = None

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_paths()
        return cls._instance

    def _init_paths(self) -> None:
        settings = get_settings()
        self.users_file = Path(settings.get("USERS_FILE"))
        self.portfolios_file = Path(settings.get("PORTFOLIOS_FILE"))
        self.rates_file = Path(settings.get("RATES_FILE"))
        self.exchange_history_file = Path(
            settings.get("EXCHANGE_HISTORY_FILE")
        )

    def load_users(self) -> List[User]:
        if not self.users_file.exists():
            return []
        try:
            with self.users_file.open("r", encoding="utf-8") as f:
                raw = json.load(f)
        except json.JSONDecodeError:
            return []
        return [User.from_json(item) for item in raw]

    def save_users(self, users: List[User]) -> None:
        data = [u.to_json() for u in users]
        tmp = self.users_file.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(self.users_file)

    def load_portfolios(self) -> List[Portfolio]:
        if not self.portfolios_file.exists():
            return []
        try:
            with self.portfolios_file.open("r", encoding="utf-8") as f:
                raw = json.load(f)
        except json.JSONDecodeError:
            return []
        return [Portfolio.from_json(item) for item in raw]

    def save_portfolios(self, portfolios: List[Portfolio]) -> None:
        data = [p.to_json() for p in portfolios]
        tmp = self.portfolios_file.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(self.portfolios_file)

    def load_rates_snapshot(self) -> dict:
        if not self.rates_file.exists():
            return {"pairs": {}, "last_refresh": None}
        with self.rates_file.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save_rates_snapshot(self, data: dict) -> None:
        tmp = self.rates_file.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(self.rates_file)

    def append_exchange_record(self, record: dict) -> None:
        history: list[Any]
        if self.exchange_history_file.exists():
            with self.exchange_history_file.open(
                "r",
                encoding="utf-8",
            ) as f:
                history = json.load(f)
        else:
            history = []
        history.append(record)
        tmp = self.exchange_history_file.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        tmp.replace(self.exchange_history_file)


def get_db() -> DatabaseManager:
    return DatabaseManager()
