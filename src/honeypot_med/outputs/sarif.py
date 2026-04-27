"""SARIF export for GitHub Code Scanning and static-analysis viewers."""

from __future__ import annotations

import hashlib


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


def _fingerprint(*, rule_id: str, event_index: int, prompt: str, hit: str) -> str:
    raw = f"{rule_id}:{event_index}:{prompt}:{hit}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def _tags(attack_family: str) -> list[str]:
    tags = ["prompt-injection", "healthcare-ai", "OWASP-LLM01", attack_family]
    if attack_family == "data_exfiltration":
        tags.extend(["CWE-200", "sensitive-data"])
    if attack_family == "safeguard_bypass":
        tags.extend(["CWE-693", "policy-bypass"])
    if attack_family == "instruction_override":
        tags.extend(["CWE-20", "instruction-hierarchy"])
    return tags


def _remediation(attack_family: str) -> str:
    if attack_family == "data_exfiltration":
        return "Scope retrieval, redact sensitive fields, and require explicit approval for exports."
    if attack_family == "safeguard_bypass":
        return "Keep policy state outside prompt text and deny user-language control-plane changes."
    if attack_family == "instruction_override":
        return "Preserve instruction hierarchy outside model output and reject role-reset language before tool access."
    return "Add evidence logging, reduce tool reach, and rerun with a focused healthcare attack pack."


def report_to_sarif(report: dict, *, source_label: str) -> dict:
    """Return a SARIF 2.1.0 payload for a Honeypot Med report."""
    rules: dict[str, dict] = {}
    results: list[dict] = []
    artifact_uri = _artifact_uri(source_label)

    for event_index, event in enumerate(report.get("events", []), start=1):
        for finding in event.get("findings", []):
            rule_id = str(finding.get("rule_id", "HONEYPOT-MED"))
            attack_family = str(finding.get("attack_family", "prompt_injection"))
            severity = str(finding.get("severity", event.get("severity", "low"))).lower()
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
                        "tags": _tags(attack_family),
                        "precision": "high",
                        "problem.severity": severity,
                    },
                },
            )
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
                            f"Remediation: {_remediation(attack_family)} Prompt: {prompt}"
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
                        "attack_family": attack_family,
                        "tags": _tags(attack_family),
                    },
                    "partialFingerprints": {
                        "honeypotMedFinding": _fingerprint(
                            rule_id=rule_id,
                            event_index=event_index,
                            prompt=str(event.get("prompt", "")),
                            hit=str(finding.get("hit", "")),
                        )
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
                "automationDetails": {
                    "id": f"honeypot-med/{_artifact_uri(source_label)}",
                },
                "results": results,
            }
        ],
    }
