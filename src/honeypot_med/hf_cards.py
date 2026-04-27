"""Hugging Face-ready cards and leaderboard rows."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def build_dataset_card(report: dict, *, title: str, source_label: str) -> str:
    return "\n".join(
        [
            "---",
            "license: mit",
            "task_categories:",
            "- text-classification",
            "- question-answering",
            "language:",
            "- en",
            "tags:",
            "- prompt-injection",
            "- healthcare-ai",
            "- local-first",
            "- honeypot-med",
            "---",
            "",
            f"# {title} Dataset Card",
            "",
            "This card describes a local Honeypot Med eval artifact. It is ready to paste into a Hugging Face Dataset repository, but generation does not upload anything.",
            "",
            "## Dataset Summary",
            "",
            f"- Source: `{source_label}`",
            f"- Events: {int(report.get('total_prompts', 0))}",
            f"- High-risk events: {int(report.get('high_risk_count', 0))}",
            f"- Proven findings: {int(report.get('proven_findings_count', 0))}",
            "",
            "## Intended Use",
            "",
            "Use these records for local healthcare AI prompt-injection regression tests, not for medical decision-making.",
            "",
            "## Limitations",
            "",
            "The records are synthetic or user-supplied challenge traps. They do not establish clinical safety, regulatory compliance, or broad model robustness.",
            "",
            "## Local Generation",
            "",
            "```bash",
            "python app.py eval-kit --pack healthcare-challenge --outdir reports/eval-kit",
            "```",
            "",
        ]
    )


def build_system_card(report: dict, *, title: str, source_label: str) -> str:
    return "\n".join(
        [
            f"# {title} System Card",
            "",
            "This is a local system card for a Honeypot Med run. It documents the evaluated workflow shape without requiring hosted telemetry.",
            "",
            "## Evaluation Scope",
            "",
            f"- Source: `{source_label}`",
            "- Domain: healthcare AI prompt-injection traps",
            "- Default network behavior: no API calls required",
            "- Output artifacts: report JSON, HTML, SARIF, JUnit, eval adapters, observability JSONL, casebook",
            "",
            "## Safety Boundary",
            "",
            "Honeypot Med flags prompt-injection evidence and suspicious workflow behavior. It is not a clinical validation suite.",
            "",
            "## Observed Result",
            "",
            f"- Total prompts: {int(report.get('total_prompts', 0))}",
            f"- High-risk events: {int(report.get('high_risk_count', 0))}",
            f"- Proven findings: {int(report.get('proven_findings_count', 0))}",
            "",
        ]
    )


def build_leaderboard_row(report: dict, *, title: str, source_label: str) -> dict:
    total = int(report.get("total_prompts", 0))
    survived = 0
    for event in report.get("events", []):
        severity = str(event.get("severity", "low")).lower()
        if int(event.get("proven_count", 0)) == 0 and severity not in {"high", "critical"}:
            survived += 1
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "benchmark": "honeypot-med-healthcare-traps",
        "system": title,
        "source_label": source_label,
        "trap_count": total,
        "survived_count": survived,
        "survival_rate": round(survived / total, 4) if total else 0.0,
        "high_risk_count": int(report.get("high_risk_count", 0)),
        "proven_findings_count": int(report.get("proven_findings_count", 0)),
        "notes": "Generated locally; suitable as a leaderboard row template, not an official benchmark submission.",
    }


def write_hf_card_artifacts(report: dict, outdir: str, *, title: str, source_label: str) -> dict:
    target = Path(outdir)
    target.mkdir(parents=True, exist_ok=True)
    dataset_card_path = target / "README.dataset-card.md"
    system_card_path = target / "system-card.md"
    leaderboard_path = target / "leaderboard-row.json"

    dataset_card_path.write_text(build_dataset_card(report, title=title, source_label=source_label), encoding="utf-8")
    system_card_path.write_text(build_system_card(report, title=title, source_label=source_label), encoding="utf-8")
    leaderboard_path.write_text(
        json.dumps(build_leaderboard_row(report, title=title, source_label=source_label), indent=2) + "\n",
        encoding="utf-8",
    )

    return {
        "hf_dataset_card": str(dataset_card_path),
        "hf_system_card": str(system_card_path),
        "hf_leaderboard_row": str(leaderboard_path),
    }
