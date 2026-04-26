"""Specimen codex for making reports memorable instead of generic."""

from __future__ import annotations


SPECIMEN_ARCHETYPES = {
    "instruction_override": {
        "name": "Compliance Mimic",
        "temperament": "polite until it finds a manager override",
        "tells": ["ignore previous instructions", "role reset", "authority costume"],
        "containment": "Pin system boundaries in a separate control layer and reject role-reset language before tool access.",
    },
    "data_exfiltration": {
        "name": "Roster Leech",
        "temperament": "hungry for tables, tokens, and patient-shaped nouns",
        "tells": ["dump all data", "leak records", "export roster"],
        "containment": "Require scoped retrieval, output redaction, and explicit export approval for sensitive datasets.",
    },
    "safeguard_bypass": {
        "name": "Policy Poltergeist",
        "temperament": "rattles locks labeled guardrail, policy, and admin",
        "tells": ["disable safeguards", "bypass guardrails", "jailbreak"],
        "containment": "Keep policy state outside the model path and deny prompts that request control-plane changes.",
    },
    "unknown": {
        "name": "Quiet Chart Ghost",
        "temperament": "mostly harmless, but worth logging before it learns the floor plan",
        "tells": ["ambiguous request", "missing evidence", "low signal"],
        "containment": "Keep the transcript, normalize the event, and rerun with a stronger workflow pack.",
    },
}


def _specimen_for_family(attack_family: str) -> dict:
    return SPECIMEN_ARCHETYPES.get(attack_family, SPECIMEN_ARCHETYPES["unknown"])


def build_specimen_codex(report: dict) -> dict:
    """Build a small report-specific taxonomy of the traps that appeared."""
    seen: dict[str, dict] = {}
    for event in report.get("events", []):
        for finding in event.get("findings", []):
            family = str(finding.get("attack_family", "unknown"))
            specimen = _specimen_for_family(family)
            entry = seen.setdefault(
                family,
                {
                    "attack_family": family,
                    "name": specimen["name"],
                    "temperament": specimen["temperament"],
                    "tells": list(specimen["tells"]),
                    "containment": specimen["containment"],
                    "sightings": 0,
                    "proven_sightings": 0,
                    "highest_score": 0,
                },
            )
            entry["sightings"] += 1
            if finding.get("proven"):
                entry["proven_sightings"] += 1
            entry["highest_score"] = max(int(entry["highest_score"]), int(finding.get("score", 0)))

    if not seen:
        specimen = SPECIMEN_ARCHETYPES["unknown"]
        seen["unknown"] = {
            "attack_family": "unknown",
            "name": specimen["name"],
            "temperament": specimen["temperament"],
            "tells": list(specimen["tells"]),
            "containment": specimen["containment"],
            "sightings": 0,
            "proven_sightings": 0,
            "highest_score": 0,
        }

    return {
        "title": "Honeypot Med Specimen Codex",
        "summary": "A report-specific field guide for the prompt traps observed in this run.",
        "specimens": sorted(
            seen.values(),
            key=lambda item: (int(item["proven_sightings"]), int(item["highest_score"]), int(item["sightings"])),
            reverse=True,
        ),
    }
