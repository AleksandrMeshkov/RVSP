from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "responses.json"


def _ensure_file() -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")


def load_all() -> list[dict[str, Any]]:
    _ensure_file()
    content = DATA_FILE.read_text(encoding="utf-8")
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        data = []
    if not isinstance(data, list):
        return []
    return data


def save_one(item: dict[str, Any]) -> None:
    data = load_all()
    data.append(item)
    DATA_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
