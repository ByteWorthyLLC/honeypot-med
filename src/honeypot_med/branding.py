"""Branding asset helpers for hosted and exported artifacts."""

from __future__ import annotations

import base64
from importlib import resources


def load_default_hero_data_uri() -> str | None:
    """Return the packaged hero image as a data URI when available."""
    try:
        asset = resources.files("honeypot_med").joinpath("static").joinpath("viral-hero.jpg")
        data = asset.read_bytes()
    except (FileNotFoundError, ModuleNotFoundError):
        return None

    encoded = base64.b64encode(data).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"
