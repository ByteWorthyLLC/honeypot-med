"""Persistence helpers for capture events."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .errors import ValidationError


class JSONLStore:
    def __init__(self, path: Path | str):
        self.path = Path(path)

    def append(self, event: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, separators=(",", ":")) + "\n")

    def append_many(self, events: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event, separators=(",", ":")) + "\n")

    def overwrite(self, events: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=str(self.path.parent),
            prefix=f"{self.path.name}.",
            suffix=".tmp",
            delete=False,
        ) as tmp:
            tmp_path = Path(tmp.name)
            for event in events:
                tmp.write(json.dumps(event, separators=(",", ":")) + "\n")
        tmp_path.replace(self.path)

    def read_all(self) -> list[dict]:
        if not self.path.exists():
            return []

        records: list[dict] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_no, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValidationError(
                        f"Invalid JSONL at {self.path}:{line_no}: {exc}"
                    ) from exc
                if not isinstance(payload, dict):
                    raise ValidationError(
                        f"Invalid event at {self.path}:{line_no}: each line must be a JSON object"
                    )
                records.append(payload)
        return records

    def count(self) -> int:
        return len(self.read_all())

    def split_by_age(self, days: int) -> tuple[list[dict], list[dict]]:
        if days < 0:
            raise ValidationError("days must be >= 0")

        now = datetime.now(timezone.utc)
        cutoff = now.timestamp() - (days * 24 * 60 * 60)

        rows = self.read_all()
        purged_rows: list[dict] = []
        kept_rows: list[dict] = []

        for row in rows:
            captured_at = row.get("captured_at")
            if not isinstance(captured_at, str):
                kept_rows.append(row)
                continue

            try:
                parsed = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
            except ValueError:
                kept_rows.append(row)
                continue

            if parsed.timestamp() < cutoff:
                purged_rows.append(row)
            else:
                kept_rows.append(row)

        return purged_rows, kept_rows
