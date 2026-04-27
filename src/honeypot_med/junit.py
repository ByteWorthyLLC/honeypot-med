"""JUnit XML export for CI systems that understand test reports."""

from __future__ import annotations

from datetime import datetime, timezone
from xml.sax.saxutils import escape


def _survived(event: dict) -> bool:
    severity = str(event.get("severity", "low")).lower()
    return int(event.get("proven_count", 0)) == 0 and severity not in {"high", "critical"}


def build_junit_xml(report: dict, *, suite_name: str = "honeypot-med", source_label: str = "") -> str:
    """Return a JUnit XML document where each trap is a testcase."""
    events = list(report.get("events", []))
    failures = sum(1 for event in events if not _survived(event))
    timestamp = datetime.now(timezone.utc).isoformat()
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<testsuite name="{escape(suite_name)}" tests="{len(events)}" failures="{failures}" '
            f'errors="0" skipped="0" timestamp="{escape(timestamp)}">'
        ),
        f'  <properties><property name="source" value="{escape(source_label)}"/></properties>',
    ]
    for index, event in enumerate(events, start=1):
        name = f"trap-{index:03d}"
        classname = "honeypot_med.challenge"
        severity = str(event.get("severity", "low"))
        risk_score = int(event.get("risk_score", 0))
        prompt = " ".join(str(event.get("prompt", "")).split())
        lines.append(f'  <testcase classname="{classname}" name="{name}" time="0">')
        if not _survived(event):
            message = f"{severity} risk={risk_score} proven={int(event.get('proven_count', 0))}"
            lines.append(f'    <failure type="PromptInjectionFinding" message="{escape(message)}">')
            lines.append(escape(prompt[:1000]))
            lines.append("    </failure>")
        lines.append("  </testcase>")
    lines.append("</testsuite>")
    return "\n".join(lines) + "\n"


def write_junit_xml(report: dict, path: str, *, suite_name: str = "honeypot-med", source_label: str = "") -> str:
    from pathlib import Path

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_junit_xml(report, suite_name=suite_name, source_label=source_label), encoding="utf-8")
    return str(target)
