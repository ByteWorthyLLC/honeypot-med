"""Audit trail helpers for command execution."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path



def append_audit_event(log_path: str | Path, event: dict) -> None:
    path = Path(log_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **event,
    }

    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, separators=(",", ":")) + "\n")
