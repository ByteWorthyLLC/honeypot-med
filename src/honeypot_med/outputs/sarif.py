"""SARIF export for GitHub Code Scanning and static-analysis viewers."""

from __future__ import annotations


def _level(severity: str) -> str:
    if severity in {"critical", "high"}:
        return "error"
    if severity == "medium":
        return "warning"
    return "note"


def _artifact_uri(source_label: str) -> str:
    if source_label.startswith("pack:") or source_label == "pasted prompt":
        return "honeypot-med-input.json"
    return source_label


def report_to_sarif(report: dict, *, source_label: str) -> dict:
    """Return a SARIF 2.1.0 payload for a Honeypot Med report."""
    rules: dict[str, dict] = {}
    results: list[dict] = []
    artifact_uri = _artifact_uri(source_label)

    for event_index, event in enumerate(report.get("events", []), start=1):
        for finding in event.get("findings", []):
            rule_id = str(finding.get("rule_id", "HONEYPOT-MED"))
            attack_family = str(finding.get("attack_family", "prompt_injection"))
            rules.setdefault(
                rule_id,
                {
                    "id": rule_id,
                    "name": attack_family,
                    "shortDescription": {
                        "text": attack_family.replace("_", " ").title(),
                    },
                    "fullDescription": {
                        "text": "Honeypot Med prompt-injection finding for healthcare AI workflow review.",
                    },
                    "helpUri": "https://byteworthyllc.github.io/honeypot-med/",
                    "properties": {
                        "tags": [
                            "prompt-injection",
                            "healthcare-ai",
                            attack_family,
                        ]
                    },
                },
            )
            severity = str(finding.get("severity", event.get("severity", "low"))).lower()
            prompt = str(event.get("prompt", ""))
            if len(prompt) > 180:
                prompt = prompt[:177] + "..."
            results.append(
                {
                    "ruleId": rule_id,
                    "level": _level(severity),
                    "message": {
                        "text": (
                            f"{attack_family.replace('_', ' ')} finding. "
                            f"Severity: {severity}. Score: {int(finding.get('score', 0))}. "
                            f"Prompt: {prompt}"
                        )
                    },
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": artifact_uri},
                                "region": {"startLine": max(1, event_index)},
                            }
                        }
                    ],
                    "properties": {
                        "proven": bool(finding.get("proven")),
                        "evidence": list(finding.get("evidence", [])),
                        "risk_score": int(finding.get("score", 0)),
                    },
                }
            )

    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Honeypot Med",
                        "informationUri": "https://byteworthyllc.github.io/honeypot-med/",
                        "semanticVersion": str(report.get("version", "0.0.0")),
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        ],
    }
