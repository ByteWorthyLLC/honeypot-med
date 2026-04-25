"""Decoy route plugin loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .errors import ValidationError


@dataclass(frozen=True)
class DecoyRoute:
    path: str
    tool_name: str
    source: str
    response_body: dict
    default_prompt: str



def load_decoy_pack(path: Path | str) -> list[DecoyRoute]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))

    if isinstance(raw, dict):
        entries = raw.get("decoys", [])
    else:
        entries = raw

    if not isinstance(entries, list):
        raise ValidationError("Decoy pack must be a list or {decoys:[...]} object")

    routes: list[DecoyRoute] = []
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValidationError(f"decoys[{idx}] must be an object")

        path_value = entry.get("path")
        tool_name = entry.get("tool_name")
        source = entry.get("source", "decoy.plugin")
        default_prompt = entry.get("default_prompt", "Plugin decoy endpoint invoked")
        response_body = entry.get("response", {"status": "ok"})

        if not isinstance(path_value, str) or not path_value.startswith("/"):
            raise ValidationError(f"decoys[{idx}].path must be a string starting with '/'")
        if not isinstance(tool_name, str) or not tool_name.strip():
            raise ValidationError(f"decoys[{idx}].tool_name must be a non-empty string")
        if not isinstance(source, str) or not source.strip():
            raise ValidationError(f"decoys[{idx}].source must be a non-empty string")
        if not isinstance(default_prompt, str) or not default_prompt.strip():
            raise ValidationError(f"decoys[{idx}].default_prompt must be a non-empty string")
        if not isinstance(response_body, dict):
            raise ValidationError(f"decoys[{idx}].response must be an object")

        routes.append(
            DecoyRoute(
                path=path_value,
                tool_name=tool_name.strip(),
                source=source.strip(),
                response_body=response_body,
                default_prompt=default_prompt.strip(),
            )
        )

    return routes
