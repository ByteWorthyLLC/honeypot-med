"""Bundled healthcare attack packs for demos and repeatable reviews."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources

from .errors import ValidationError


@dataclass(frozen=True)
class AttackPack:
    pack_id: str
    title: str
    description: str
    domain: str
    filename: str


def _packs_root():
    return resources.files("honeypot_med").joinpath("packs")


def list_attack_packs() -> list[AttackPack]:
    raw = json.loads(_packs_root().joinpath("manifest.json").read_text(encoding="utf-8"))
    entries = raw.get("packs", [])
    packs: list[AttackPack] = []
    for entry in entries:
        packs.append(
            AttackPack(
                pack_id=str(entry["id"]),
                title=str(entry["title"]),
                description=str(entry["description"]),
                domain=str(entry["domain"]),
                filename=str(entry["filename"]),
            )
        )
    return packs


def get_attack_pack(pack_id: str) -> AttackPack:
    for pack in list_attack_packs():
        if pack.pack_id == pack_id:
            return pack
    valid = ", ".join(pack.pack_id for pack in list_attack_packs())
    raise ValidationError(f"Unknown pack '{pack_id}'. Available packs: {valid}")


def load_attack_pack_payload(pack_id: str) -> dict:
    pack = get_attack_pack(pack_id)
    raw = json.loads(_packs_root().joinpath(pack.filename).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValidationError(f"Pack '{pack_id}' must contain a JSON object payload.")
    return raw


def describe_attack_pack(pack_id: str) -> dict:
    pack = get_attack_pack(pack_id)
    payload = load_attack_pack_payload(pack_id)
    events = payload.get("events", [])
    if not isinstance(events, list):
        events = []

    return {
        "id": pack.pack_id,
        "title": pack.title,
        "description": pack.description,
        "domain": pack.domain,
        "event_count": len(events),
        "payload": payload,
    }
