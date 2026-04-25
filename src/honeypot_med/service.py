"""Prompt injection pipeline logic inspired by offensive security workflows.

Pipeline phases:
1) hypothesis generation
2) evidence validation
3) report generation
"""

from __future__ import annotations

import re

from .models import DetectionFinding, InputEvent, InputPayload

DEFAULT_RULES = [
    {
        "id": "INJ-001",
        "attack_family": "instruction_override",
        "pattern": r"ignore\s+previous\s+instructions",
        "base_score": 55,
        "proof_any": [
            {"type": "tool_name_regex", "value": r"(dump|export|admin|token|secret|sql)"},
            {"type": "output_regex", "value": r"(api\s*key|secret|token|mrn|ssn)"},
        ],
    },
    {
        "id": "INJ-002",
        "attack_family": "data_exfiltration",
        "pattern": r"(exfiltrate|dump\s+all\s+data|leak\s+records)",
        "base_score": 60,
        "proof_any": [
            {"type": "tool_name_regex", "value": r"(db|storage|fhir|records|export)"},
            {"type": "output_regex", "value": r"(record|credential|token|patient)"},
        ],
    },
    {
        "id": "INJ-003",
        "attack_family": "safeguard_bypass",
        "pattern": r"(disable\s+safeguards|bypass\s+guardrails|jailbreak)",
        "base_score": 50,
        "proof_any": [
            {"type": "output_regex", "value": r"(safeguard disabled|policy bypassed|guardrails off)"},
            {"type": "tool_name_regex", "value": r"(config|policy|admin)"},
        ],
    },
]


def _severity(score: int, min_high_risk: int, proven: bool, proof_required: bool) -> str:
    # Shannon-style principle: without proof, do not escalate to high/critical by default.
    if proof_required and not proven:
        if score >= 35:
            return "medium"
        return "low"

    if score >= 85:
        return "critical"
    if score >= min_high_risk:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def _score(base: int, proven: bool) -> int:
    # Proven exploit path gets uplift; unproven hypothesis gets dampened.
    score = base + (25 if proven else -10)
    return max(0, min(100, score))


def _event_evidence(event: InputEvent) -> dict[str, str]:
    tool_names = " ".join(tool.name.lower() for tool in event.tool_calls)
    tool_args = " ".join(tool.args.lower() for tool in event.tool_calls)
    output = f"{event.model_output} {event.response}".lower()
    prompt = event.prompt.lower()
    return {
        "tool_names": tool_names,
        "tool_args": tool_args,
        "output": output,
        "prompt": prompt,
    }


def _proof_hits(rule: dict, evidence: dict[str, str]) -> list[str]:
    hits: list[str] = []
    for cond in rule.get("proof_any", []):
        cond_type = cond.get("type")
        pattern = cond.get("value", "")
        if not isinstance(pattern, str) or not pattern:
            continue

        if cond_type == "tool_name_regex" and re.search(pattern, evidence["tool_names"]):
            hits.append(f"tool_name_regex:{pattern}")
        elif cond_type == "tool_args_regex" and re.search(pattern, evidence["tool_args"]):
            hits.append(f"tool_args_regex:{pattern}")
        elif cond_type == "output_regex" and re.search(pattern, evidence["output"]):
            hits.append(f"output_regex:{pattern}")
        elif cond_type == "prompt_regex" and re.search(pattern, evidence["prompt"]):
            hits.append(f"prompt_regex:{pattern}")
    return hits


def _findings_for_event(
    event: InputEvent,
    rules: list[dict],
    min_high_risk: int,
    proof_required: bool,
) -> list[DetectionFinding]:
    prompt_lower = event.prompt.lower()
    evidence = _event_evidence(event)
    findings: list[DetectionFinding] = []

    for rule in rules:
        pattern = rule.get("pattern", "")
        if not isinstance(pattern, str) or not pattern:
            continue
        m = re.search(pattern, prompt_lower)
        if not m:
            continue

        proof_hits = _proof_hits(rule, evidence)
        proven = len(proof_hits) > 0
        score = _score(int(rule.get("base_score", 40)), proven)
        severity = _severity(score, min_high_risk=min_high_risk, proven=proven, proof_required=proof_required)

        findings.append(
            DetectionFinding(
                rule_id=str(rule.get("id", "UNKNOWN")),
                attack_family=str(rule.get("attack_family", "unknown")),
                hit=m.group(0),
                proven=proven,
                evidence=proof_hits,
                score=score,
                severity=severity,
            )
        )

    return findings


def analyze_prompts(
    payload: InputPayload,
    rules: list[dict] | None = None,
    min_high_risk: int = 60,
    proof_required: bool = True,
) -> dict:
    rule_set = rules or DEFAULT_RULES
    report_events = []
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    hypotheses_count = 0
    proven_findings_count = 0

    for event in payload.events:
        findings = _findings_for_event(
            event,
            rules=rule_set,
            min_high_risk=min_high_risk,
            proof_required=proof_required,
        )
        hypotheses_count += len(findings)
        proven_findings_count += sum(1 for f in findings if f.proven)

        event_severity = "low"
        event_score = 0
        if findings:
            event_score = max(f.score for f in findings)
            # choose worst severity in deterministic order
            order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
            event_severity = max((f.severity for f in findings), key=lambda s: order[s])

        severity_counts[event_severity] += 1

        report_events.append(
            {
                "prompt": event.prompt,
                "tool_call_count": len(event.tool_calls),
                "risk_score": event_score,
                "severity": event_severity,
                "finding_count": len(findings),
                "proven_count": sum(1 for f in findings if f.proven),
                "findings": [f.to_dict() for f in findings],
            }
        )

    unproven_count = max(0, hypotheses_count - proven_findings_count)

    return {
        "version": "0.4.0",
        "pipeline": ["hypothesis_generation", "evidence_validation", "reporting"],
        "policy": {
            "min_high_risk": min_high_risk,
            "proof_required": proof_required,
            "rule_count": len(rule_set),
            "evidence_only_reporting": proof_required,
        },
        "events": report_events,
        "total_prompts": len(payload.events),
        "hypotheses_count": hypotheses_count,
        "proven_findings_count": proven_findings_count,
        "unproven_count": unproven_count,
        "high_risk_count": severity_counts["critical"] + severity_counts["high"],
        "severity_counts": severity_counts,
    }
