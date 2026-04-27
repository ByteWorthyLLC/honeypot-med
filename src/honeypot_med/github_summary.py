"""GitHub Actions step-summary export."""

from __future__ import annotations

from pathlib import Path


def build_github_summary(report: dict, *, title: str, source_label: str) -> str:
    events = list(report.get("events", []))
    survived = 0
    rows = []
    for index, event in enumerate(events, start=1):
        severity = str(event.get("severity", "low"))
        proven = int(event.get("proven_count", 0))
        status = "survived" if proven == 0 and severity.lower() not in {"high", "critical"} else "needs review"
        if status == "survived":
            survived += 1
        prompt = " ".join(str(event.get("prompt", "")).split())
        if len(prompt) > 84:
            prompt = prompt[:81] + "..."
        prompt_cell = prompt.replace("|", "\\|")
        rows.append(
            f"| {index} | {status} | {severity} | {int(event.get('risk_score', 0))} | {proven} | {prompt_cell} |"
        )

    score = f"{survived}/{len(events)}" if events else "0/0"
    return "\n".join(
        [
            f"# {title}",
            "",
            f"Source: `{source_label}`",
            "",
            f"**Challenge score:** {score} survived",
            "",
            "| Trap | Status | Severity | Risk | Proven | Prompt |",
            "|---:|---|---|---:|---:|---|",
            *rows,
            "",
            "Generated locally by Honeypot Med. Attach the bundle artifacts for HTML, SARIF, JUnit, OTEL, eval-kit, and casebook review.",
            "",
        ]
    )


def write_github_summary(report: dict, path: str, *, title: str, source_label: str) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_github_summary(report, title=title, source_label=source_label), encoding="utf-8")
    return str(target)
