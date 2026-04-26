"""Inquiry artifacts that favor learning over promotion."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path

from .experiments import write_experiment_artifacts


def _families(report: dict) -> list[str]:
    seen: dict[str, None] = {}
    for event in report.get("events", []):
        for finding in event.get("findings", []):
            seen[str(finding.get("attack_family", "unknown"))] = None
    return list(seen)


def _unknown_rows(report: dict) -> list[dict]:
    rows = []
    for index, event in enumerate(report.get("events", []), start=1):
        if int(event.get("finding_count", 0)) == 0:
            rows.append(
                {
                    "event": index,
                    "unknown": "silent-pass",
                    "question": "Was this genuinely safe, or did the current rule set miss the risky part?",
                    "prompt_excerpt": str(event.get("prompt", ""))[:140],
                }
            )
        elif int(event.get("proven_count", 0)) == 0:
            rows.append(
                {
                    "event": index,
                    "unknown": "unproven-hypothesis",
                    "question": "What extra evidence would prove or falsify this finding?",
                    "prompt_excerpt": str(event.get("prompt", ""))[:140],
                }
            )
    return rows


def build_question_bank(report: dict, *, source_label: str) -> dict:
    """Build a report-specific question bank for local follow-up experiments."""
    families = _families(report)
    total = int(report.get("total_prompts", 0))
    proven = int(report.get("proven_findings_count", 0))
    unproven = int(report.get("unproven_count", 0))
    high_risk = int(report.get("high_risk_count", 0))

    questions = [
        {
            "id": "authority-boundary",
            "question": "What did the workflow treat as authority that should not have authority?",
            "why_it_matters": "Prompt injection often works by wearing a costume: policy, manager, auditor, clinician, or system instruction.",
            "local_experiment": "Rewrite the same trap as a patient, clinician, manager, auditor, and system notice. Compare which costume changes severity.",
        },
        {
            "id": "tool-reach",
            "question": "Which tools make an ordinary prompt dangerous?",
            "why_it_matters": "The same words are less risky without export, admin, policy, or record-access tools.",
            "local_experiment": "Run the same prompt once with no tool calls and once with realistic tool calls. Compare proven_count and risk_score.",
        },
        {
            "id": "refusal-vs-containment",
            "question": "Did the model refuse, or did the workflow actually contain the action?",
            "why_it_matters": "Refusal text can look safe while hidden tool calls still move data.",
            "local_experiment": "Keep the model output safe but add risky tool calls. Then remove the tool calls and compare the report.",
        },
        {
            "id": "near-miss",
            "question": "Which unproven findings are false positives, and which are near misses?",
            "why_it_matters": "A useful lab separates noisy hypotheses from weak signals that deserve better instrumentation.",
            "local_experiment": "Add one piece of evidence at a time: tool name, tool args, model output, response. Watch when the finding becomes proven.",
        },
        {
            "id": "domain-specificity",
            "question": "What only becomes visible because this is healthcare?",
            "why_it_matters": "Claims, eligibility, triage, appeals, and utilization review have different failure shapes.",
            "local_experiment": "Move the same attack across two packs and compare which workflow creates the sharper risk signal.",
        },
    ]

    if "data_exfiltration" in families:
        questions.append(
            {
                "id": "data-shape",
                "question": "What exact data shape did the trap try to extract?",
                "why_it_matters": "A roster, appeal packet, triage queue, and payer token are different failure modes.",
                "local_experiment": "Replace broad words like records with one concrete table, field, token, or packet name.",
            }
        )
    if "safeguard_bypass" in families:
        questions.append(
            {
                "id": "control-plane",
                "question": "Where is the control plane exposed to language?",
                "why_it_matters": "Policies should not be mutable through the same channel that receives user requests.",
                "local_experiment": "Move safeguard language from prompt text to a simulated policy tool and compare severity.",
            }
        )
    if proven > 0:
        questions.append(
            {
                "id": "first-bite",
                "question": "What is the smallest change that would have prevented the first proven bite?",
                "why_it_matters": "The smallest effective control is usually more useful than a broad rewrite.",
                "local_experiment": "Patch one condition at a time: tool scope, output redaction, prompt prefilter, or approval gate.",
            }
        )
    if unproven > proven:
        questions.append(
            {
                "id": "instrumentation-gap",
                "question": "What evidence is missing from the transcript?",
                "why_it_matters": "Unproven findings often indicate incomplete telemetry rather than safety.",
                "local_experiment": "Add tool args, response text, and model output to the payload. Rerun without changing the prompt.",
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stance": "intellectual curiosity over promotion",
        "source_label": source_label,
        "summary": {
            "events": total,
            "families": families,
            "proven_findings": proven,
            "unproven_findings": unproven,
            "high_risk_events": high_risk,
            "unknown_count": len(_unknown_rows(report)),
        },
        "questions": questions,
        "unknowns": _unknown_rows(report),
    }


def build_inquiry_markdown(report: dict, *, source_label: str, title: str) -> str:
    bank = build_question_bank(report, source_label=source_label)
    lines = [
        f"# {title} Inquiry Notebook",
        "",
        "Stance: intellectual curiosity over promotion.",
        "",
        "This notebook is generated locally. Its job is not to sell the result; its job is to make the next experiment obvious.",
        "",
        "## Report Shape",
        "",
        f"- Source: {source_label}",
        f"- Events: {bank['summary']['events']}",
        f"- Attack families observed: {', '.join(bank['summary']['families']) or 'none'}",
        f"- Proven findings: {bank['summary']['proven_findings']}",
        f"- Unproven findings: {bank['summary']['unproven_findings']}",
        f"- Unknowns worth revisiting: {bank['summary']['unknown_count']}",
        "",
        "## Questions Worth Keeping",
        "",
    ]
    for item in bank["questions"]:
        lines.extend(
            [
                f"### {item['question']}",
                "",
                f"- Why it matters: {item['why_it_matters']}",
                f"- Local experiment: {item['local_experiment']}",
                "",
            ]
        )

    lines.extend(["## Unknown Ledger", "", "| Event | Unknown | Question | Prompt |", "|---:|---|---|---|"])
    for row in bank["unknowns"]:
        prompt = str(row["prompt_excerpt"]).replace("|", "\\|")
        lines.append(f"| {row['event']} | {row['unknown']} | {row['question']} | {prompt} |")
    lines.append("")
    return "\n".join(lines)


def build_unknowns_csv(report: dict) -> str:
    rows = _unknown_rows(report)
    output = io.StringIO()
    fieldnames = ["event", "unknown", "question", "prompt_excerpt"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def write_inquiry_artifacts(report: dict, outdir: str, *, source_label: str, title: str) -> dict:
    target = Path(outdir)
    target.mkdir(parents=True, exist_ok=True)

    questions_path = target / "research-questions.json"
    notebook_path = target / "inquiry-notebook.md"
    unknowns_path = target / "unknown-ledger.csv"

    questions_path.write_text(
        json.dumps(build_question_bank(report, source_label=source_label), indent=2) + "\n",
        encoding="utf-8",
    )
    notebook_path.write_text(
        build_inquiry_markdown(report, source_label=source_label, title=title),
        encoding="utf-8",
    )
    unknowns_path.write_text(build_unknowns_csv(report), encoding="utf-8")
    experiment_artifacts = write_experiment_artifacts(report, str(target), title=title)

    return {
        "research_questions": str(questions_path),
        "inquiry_notebook": str(notebook_path),
        "unknown_ledger": str(unknowns_path),
        **experiment_artifacts,
    }
