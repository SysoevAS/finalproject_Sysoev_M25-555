from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .exceptions import CurrencyNotFoundError
from . import currencies


def validate_currency_code(code: str) -> str:
    if not code:
        raise CurrencyNotFoundError(code="")
    normalized = code.upper()
    currencies.get_currency(normalized)
    return normalized


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp_path.replace(path)
