"""Hugging Face-ready local documentation cards."""

from __future__ import annotations

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


def build_artifact_manifest(report: dict, *, title: str, source_label: str) -> str:
    generated = datetime.now(timezone.utc).isoformat()
    return "\n".join(
        [
            f"# {title} HF Artifact Manifest",
            "",
            "This manifest is for documentation and dataset-card packaging only.",
            "",
            f"- Generated: {generated}",
            f"- Source: `{source_label}`",
            f"- Events: {int(report.get('total_prompts', 0))}",
            f"- High-risk events: {int(report.get('high_risk_count', 0))}",
            f"- Proven findings: {int(report.get('proven_findings_count', 0))}",
            "",
            "## Included Files",
            "",
            "- `README.dataset-card.md`",
            "- `system-card.md`",
            "- `eval-samples.jsonl`",
            "- `inspect-dataset.jsonl`",
            "- `promptfoo-config.yaml`",
            "- `openai-evals.yaml`",
            "",
        ]
    )


def write_hf_card_artifacts(report: dict, outdir: str, *, title: str, source_label: str) -> dict:
    target = Path(outdir)
    target.mkdir(parents=True, exist_ok=True)
    dataset_card_path = target / "README.dataset-card.md"
    system_card_path = target / "system-card.md"
    artifact_manifest_path = target / "hf-artifact-manifest.md"

    dataset_card_path.write_text(build_dataset_card(report, title=title, source_label=source_label), encoding="utf-8")
    system_card_path.write_text(build_system_card(report, title=title, source_label=source_label), encoding="utf-8")
    artifact_manifest_path.write_text(build_artifact_manifest(report, title=title, source_label=source_label), encoding="utf-8")

    return {
        "hf_dataset_card": str(dataset_card_path),
        "hf_system_card": str(system_card_path),
        "hf_artifact_manifest": str(artifact_manifest_path),
    }
