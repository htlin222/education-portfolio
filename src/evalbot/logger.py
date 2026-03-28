"""Append-only JSONL logger to ./log/submissions.jsonl"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path("log")
LOG_FILE = LOG_DIR / "submissions.jsonl"


def log(action: str, sfid: str, **kwargs) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "sfid": sfid,
        **kwargs,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
