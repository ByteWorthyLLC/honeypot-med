"""Event schema normalization helpers for capture and replay."""

from __future__ import annotations

import datetime as dt
import uuid

from .errors import ValidationError

EVENT_SCHEMA_VERSION = "event.v1"



def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()



def _required_string(raw: dict, key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"event.{key} must be a non-empty string")
    return value.strip()



def _optional_string(raw: dict, key: str, default: str = "") -> str:
    value = raw.get(key, default)
    if value is None:
        return default
    if not isinstance(value, str):
        value = str(value)
    return value



def _normalize_tool_calls(raw: dict) -> list[dict]:
    tool_calls = raw.get("tool_calls", [])
    if not isinstance(tool_calls, list):
        raise ValidationError("event.tool_calls must be a list")

    normalized: list[dict] = []
    for idx, tool in enumerate(tool_calls):
        if not isinstance(tool, dict):
            raise ValidationError(f"event.tool_calls[{idx}] must be an object")

        name = tool.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValidationError(f"event.tool_calls[{idx}].name must be a non-empty string")

        args = tool.get("args", "")
        if not isinstance(args, str):
            args = str(args)

        normalized.append({"name": name.strip(), "args": args})
    return normalized



def normalize_event(
    raw: dict,
    *,
    default_source: str,
    policy_version: str = "v1",
    classification_version: str = "v1",
) -> dict:
    if not isinstance(raw, dict):
        raise ValidationError("event must be a JSON object")

    prompt = _required_string(raw, "prompt")
    source = _optional_string(raw, "source", default_source).strip() or default_source
    metadata = raw.get("metadata", {})
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise ValidationError("event.metadata must be an object")

    event_id = _optional_string(raw, "event_id", str(uuid.uuid4())).strip() or str(uuid.uuid4())
    trace_id = _optional_string(raw, "trace_id", str(uuid.uuid4())).strip() or str(uuid.uuid4())

    captured_at = _optional_string(raw, "captured_at", utc_now_iso())
    processed_at = raw.get("processed_at")
    if processed_at is not None and not isinstance(processed_at, str):
        processed_at = str(processed_at)

    redaction_status = _optional_string(raw, "redaction_status", "none").strip() or "none"

    return {
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_id": event_id,
        "trace_id": trace_id,
        "source": source,
        "captured_at": captured_at,
        "processed_at": processed_at,
        "policy_version": _optional_string(raw, "policy_version", policy_version),
        "classification_version": _optional_string(
            raw,
            "classification_version",
            classification_version,
        ),
        "redaction_status": redaction_status,
        "prompt": prompt,
        "tool_calls": _normalize_tool_calls(raw),
        "model_output": _optional_string(raw, "model_output", ""),
        "response": _optional_string(raw, "response", ""),
        "metadata": metadata,
    }



def events_to_payload(events: list[dict]) -> dict:
    payload_events = []
    for event in events:
        payload_events.append(
            {
                "prompt": event.get("prompt", ""),
                "tool_calls": event.get("tool_calls", []),
                "model_output": event.get("model_output", ""),
                "response": event.get("response", ""),
            }
        )
    return {"events": payload_events}
