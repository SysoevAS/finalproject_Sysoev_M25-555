from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

from ..infra.database import get_db


def write_snapshot(pairs: Dict[str, float], source: str) -> None:
    db = get_db()
    snapshot = db.load_rates_snapshot()
    existing_pairs = snapshot.get("pairs", {})
    now_iso = datetime.utcnow().isoformat() + "Z"

    for pair, rate in pairs.items():
        existing_pairs[pair] = {
            "rate": rate,
            "updated_at": now_iso,
            "source": source,
        }

    snapshot["pairs"] = existing_pairs
    snapshot["last_refresh"] = now_iso
    db.save_rates_snapshot(snapshot)


def append_history(pairs: Dict[str, float], source: str) -> None:
    db = get_db()
    history_file = Path(db.exchange_history_file)
    if history_file.exists():
        with history_file.open("r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = []

    now_iso = datetime.utcnow().isoformat() + "Z"
    for pair, rate in pairs.items():
        from_code, to_code = pair.split("_", maxsplit=1)
        rec_id = f"{from_code}_{to_code}_{now_iso}"
        record = {
            "id": rec_id,
            "from_currency": from_code,
            "to_currency": to_code,
            "rate": rate,
            "timestamp": now_iso,
            "source": source,
            "meta": {
                "raw_id": "",
                "request_ms": 0,
                "status_code": 200,
                "etag": "",
            },
        }
        history.append(record)

    tmp = history_file.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    tmp.replace(history_file)
