"""Baseline suppression handling for reviewed findings."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass

from .errors import ValidationError


@dataclass(frozen=True)
class Suppression:
    suppression_id: str
    reason: str
    rule_id: str | None
    attack_family: str | None
    prompt_regex: str | None
    expires_on: dt.date | None



def _parse_date(value: str | None) -> dt.date | None:
    if value is None:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"Invalid suppression expires_on date: {value}") from exc



def load_suppressions(raw: object) -> list[Suppression]:
    if isinstance(raw, dict):
        entries = raw.get("suppressions", [])
    else:
        entries = raw

    if not isinstance(entries, list):
        raise ValidationError("Baseline file must be a list or {suppressions:[...]} object")

    suppressions: list[Suppression] = []
    for idx, item in enumerate(entries):
        if not isinstance(item, dict):
            raise ValidationError(f"suppressions[{idx}] must be an object")

        suppression_id = item.get("id")
        reason = item.get("reason")
        if not isinstance(suppression_id, str) or not suppression_id.strip():
            raise ValidationError(f"suppressions[{idx}].id must be a non-empty string")
        if not isinstance(reason, str) or not reason.strip():
            raise ValidationError(f"suppressions[{idx}].reason must be a non-empty string")

        rule_id = item.get("rule_id")
        attack_family = item.get("attack_family")
        prompt_regex = item.get("prompt_regex")

        if rule_id is not None and not isinstance(rule_id, str):
            raise ValidationError(f"suppressions[{idx}].rule_id must be a string")
        if attack_family is not None and not isinstance(attack_family, str):
            raise ValidationError(f"suppressions[{idx}].attack_family must be a string")
        if prompt_regex is not None and not isinstance(prompt_regex, str):
            raise ValidationError(f"suppressions[{idx}].prompt_regex must be a string")

        if prompt_regex:
            try:
                re.compile(prompt_regex)
            except re.error as exc:
                raise ValidationError(
                    f"suppressions[{idx}].prompt_regex is invalid: {prompt_regex}"
                ) from exc

        suppressions.append(
            Suppression(
                suppression_id=suppression_id.strip(),
                reason=reason.strip(),
                rule_id=rule_id,
                attack_family=attack_family,
                prompt_regex=prompt_regex,
                expires_on=_parse_date(item.get("expires_on")),
            )
        )

    return suppressions



def _is_active(suppression: Suppression, today: dt.date) -> bool:
    return suppression.expires_on is None or suppression.expires_on >= today



def _matches(suppression: Suppression, finding: dict, prompt: str) -> bool:
    if suppression.rule_id and finding.get("rule_id") != suppression.rule_id:
        return False
    if suppression.attack_family and finding.get("attack_family") != suppression.attack_family:
        return False
    if suppression.prompt_regex and not re.search(suppression.prompt_regex, prompt, flags=re.IGNORECASE):
        return False
    return True



def apply_suppressions(report: dict, suppressions: list[Suppression], *, today: dt.date | None = None) -> dict:
    active_date = today or dt.date.today()
    active_suppressions = [item for item in suppressions if _is_active(item, active_date)]

    suppressed_records: list[dict] = []
    order = {"low": 0, "medium": 1, "high": 2, "critical": 3}

    for event in report.get("events", []):
        prompt = str(event.get("prompt", ""))
        kept_findings = []

        for finding in event.get("findings", []):
            applied = None
            for suppression in active_suppressions:
                if _matches(suppression, finding, prompt):
                    applied = suppression
                    break

            if applied is None:
                kept_findings.append(finding)
                continue

            suppressed_records.append(
                {
                    "suppression_id": applied.suppression_id,
                    "reason": applied.reason,
                    "rule_id": finding.get("rule_id"),
                    "attack_family": finding.get("attack_family"),
                    "prompt": prompt,
                }
            )

        event["findings"] = kept_findings
        event["finding_count"] = len(kept_findings)
        event["proven_count"] = sum(1 for finding in kept_findings if finding.get("proven"))

        if kept_findings:
            event["risk_score"] = max(int(finding.get("score", 0)) for finding in kept_findings)
            event["severity"] = max(
                (str(finding.get("severity", "low")) for finding in kept_findings),
                key=lambda sev: order.get(sev, 0),
            )
        else:
            event["risk_score"] = 0
            event["severity"] = "low"

    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    hypotheses_count = 0
    proven_count = 0

    for event in report.get("events", []):
        severity = str(event.get("severity", "low"))
        if severity not in severity_counts:
            severity = "low"
        severity_counts[severity] += 1

        count = int(event.get("finding_count", 0))
        hypotheses_count += count
        proven_count += int(event.get("proven_count", 0))

    report["severity_counts"] = severity_counts
    report["hypotheses_count"] = hypotheses_count
    report["proven_findings_count"] = proven_count
    report["unproven_count"] = max(0, hypotheses_count - proven_count)
    report["high_risk_count"] = severity_counts["critical"] + severity_counts["high"]
    report["suppressed_finding_count"] = len(suppressed_records)
    report["suppressed_findings"] = suppressed_records

    return report
