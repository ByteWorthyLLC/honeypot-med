"""Basic redaction policy applied before persistence."""

from __future__ import annotations

import re

REDACTION_PATTERNS = [
    (re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)([A-Za-z0-9._-]{6,})"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(token\s*[:=]\s*)([A-Za-z0-9._-]{6,})"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(secret\s*[:=]\s*)([A-Za-z0-9._-]{6,})"), r"\1[REDACTED]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED-SSN]"),
]



def redact_text(text: str) -> tuple[str, int]:
    current = text
    hits = 0
    for pattern, replacement in REDACTION_PATTERNS:
        updated, count = pattern.subn(replacement, current)
        current = updated
        hits += count
    return current, hits



def redact_event(raw_event: dict) -> tuple[dict, int]:
    event = dict(raw_event)
    total_hits = 0

    for key in ("prompt", "model_output", "response"):
        value = event.get(key, "")
        if not isinstance(value, str):
            value = str(value)
        redacted, hits = redact_text(value)
        event[key] = redacted
        total_hits += hits

    tool_calls = event.get("tool_calls", [])
    if isinstance(tool_calls, list):
        normalized_tools = []
        for tool in tool_calls:
            if not isinstance(tool, dict):
                normalized_tools.append(tool)
                continue
            cleaned = dict(tool)
            args = cleaned.get("args", "")
            if not isinstance(args, str):
                args = str(args)
            redacted, hits = redact_text(args)
            cleaned["args"] = redacted
            total_hits += hits
            normalized_tools.append(cleaned)
        event["tool_calls"] = normalized_tools

    metadata = event.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    metadata = dict(metadata)
    metadata["redaction_hits"] = total_hits
    event["metadata"] = metadata
    event["redaction_status"] = "redacted" if total_hits > 0 else "none"

    return event, total_hits
