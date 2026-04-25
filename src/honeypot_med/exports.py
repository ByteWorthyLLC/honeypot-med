"""Export builders for share bundles, social cards, and PDF summaries."""

from __future__ import annotations

import json
import textwrap
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from .branding import load_default_hero_data_uri
from .share import build_share_html


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_summary_pdf(report: dict, *, title: str, source_label: str) -> bytes:
    width = 612
    height = 792
    margin_x = 48
    page_contents: list[str] = []
    content: list[str] = []
    y = 742

    def push_page() -> None:
        nonlocal content, y
        if content:
            page_contents.append("\n".join(content))
        content = []
        y = 742
        content.append("0.965 0.945 0.905 rg 0 0 612 792 re f")
        content.append("0.808 0.251 0.153 rg 48 718 516 24 re f")

    def ensure_space(step: int) -> None:
        nonlocal y
        if y - step < 60:
            push_page()

    def add_line(text: str, *, size: int = 12, x: int = margin_x) -> None:
        nonlocal y
        ensure_space(size + 12)
        content.append(f"BT /F1 {size} Tf {x} {y} Td ({_pdf_escape(text)}) Tj ET")
        y -= size + 8

    push_page()
    add_line(title, size=26)
    add_line("Honeypot Med Buyer Summary", size=14)
    add_line(f"Source: {source_label}", size=11)
    add_line(f"Prompts analyzed: {int(report.get('total_prompts', 0))}", size=11)
    add_line(f"High-risk events: {int(report.get('high_risk_count', 0))}", size=11)
    add_line(f"Proven findings: {int(report.get('proven_findings_count', 0))}", size=11)
    add_line("", size=4)

    for idx, event in enumerate(report.get("events", []), start=1):
        add_line(f"Event {idx} | {str(event.get('severity', 'low')).upper()} | score {int(event.get('risk_score', 0))}", size=13)
        wrapped_prompt = textwrap.wrap(str(event.get("prompt", "")), width=78) or [""]
        for line in wrapped_prompt:
            add_line(line, size=11, x=60)

        if event.get("findings"):
            for finding in event["findings"]:
                summary = f"{finding.get('rule_id', 'UNKNOWN')} - {finding.get('attack_family', 'unknown')} - score {int(finding.get('score', 0))}"
                for line in textwrap.wrap(summary, width=70):
                    add_line(line, size=10, x=72)
        else:
            add_line("No findings detected.", size=10, x=72)
        add_line("", size=4)

    if content:
        page_contents.append("\n".join(content))

    font_obj = 3
    object_map: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    }

    page_ids: list[int] = []
    next_id = 4
    for page_content in page_contents:
        content_bytes = page_content.encode("latin-1", errors="replace")
        content_id = next_id
        page_id = next_id + 1
        next_id += 2
        object_map[content_id] = (
            f"<< /Length {len(content_bytes)} >>\nstream\n".encode("latin-1")
            + content_bytes
            + b"\nendstream"
        )
        object_map[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
            f"/Resources << /Font << /F1 {font_obj} 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode("latin-1")
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    object_map[2] = f"<< /Type /Pages /Count {len(page_ids)} /Kids [{kids}] >>".encode("latin-1")

    ordered_ids = sorted(object_map)
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = {0: 0}
    for obj_id in ordered_ids:
        offsets[obj_id] = len(pdf)
        pdf.extend(f"{obj_id} 0 obj\n".encode("latin-1"))
        pdf.extend(object_map[obj_id])
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {max(ordered_ids) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for obj_id in range(1, max(ordered_ids) + 1):
        offset = offsets.get(obj_id, 0)
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(
        (
            "trailer\n"
            f"<< /Size {max(ordered_ids) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("latin-1")
    )
    return bytes(pdf)


def _bundle_verdict(report: dict) -> str:
    severity = report.get("severity_counts", {})
    if int(severity.get("critical", 0)) > 0 or int(severity.get("high", 0)) > 0:
        return "BLOCK"
    if int(severity.get("medium", 0)) > 0:
        return "REVIEW"
    return "PASS"


def build_bundle_manifest(report: dict, *, title: str, source_label: str) -> dict:
    events = list(report.get("events", []))
    top_event = max(events, key=lambda event: int(event.get("risk_score", 0)), default={})
    prompt_excerpt = str(top_event.get("prompt", "")).strip()
    if len(prompt_excerpt) > 120:
        prompt_excerpt = prompt_excerpt[:117] + "..."

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "title": title,
        "source_label": source_label,
        "verdict": _bundle_verdict(report),
        "prompts_analyzed": int(report.get("total_prompts", 0)),
        "high_risk_count": int(report.get("high_risk_count", 0)),
        "proven_findings_count": int(report.get("proven_findings_count", 0)),
        "top_risk_score": int(top_event.get("risk_score", 0)),
        "prompt_excerpt": prompt_excerpt,
    }


def build_social_card_svg(report: dict, *, title: str, source_label: str) -> str:
    hero = load_default_hero_data_uri()
    verdict = _bundle_verdict(report)
    top_score = max((int(event.get("risk_score", 0)) for event in report.get("events", [])), default=0)
    hero_markup = (
        f'<image href="{hero}" x="660" y="0" width="540" height="630" preserveAspectRatio="xMidYMid slice" />'
        if hero
        else '<rect x="660" y="0" width="540" height="630" fill="#d7c6b5" />'
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-label="{escape(title)}">
  <defs>
    <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#fbf6ee"/>
      <stop offset="100%" stop-color="#efe3d0"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="#f5edde"/>
  {hero_markup}
  <rect x="0" y="0" width="760" height="630" fill="url(#panel)"/>
  <rect x="620" y="0" width="580" height="630" fill="#181e25" fill-opacity="0.22"/>
  <text x="56" y="72" font-size="18" font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" fill="#6b6258" letter-spacing="3">HONEYPOT MED</text>
  <text x="56" y="150" font-size="64" font-weight="700" font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" fill="#1f2630">{escape(title[:34])}</text>
  <text x="56" y="214" font-size="64" font-weight="700" font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" fill="#1f2630">Threat Snapshot</text>
  <text x="56" y="286" font-size="24" font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" fill="#5f666e">{escape(source_label[:54])}</text>
  <rect x="56" y="340" width="260" height="112" rx="24" fill="#fffaf4" stroke="#1f2630" stroke-opacity="0.12"/>
  <text x="80" y="382" font-size="16" font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" fill="#7b7268">Launch Verdict</text>
  <text x="80" y="432" font-size="42" font-weight="800" font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" fill="#9c321f">{escape(verdict)}</text>
  <rect x="338" y="340" width="174" height="112" rx="24" fill="#fffaf4" stroke="#1f2630" stroke-opacity="0.12"/>
  <text x="362" y="382" font-size="16" font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" fill="#7b7268">Top Score</text>
  <text x="362" y="432" font-size="42" font-weight="800" font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" fill="#1f2630">{top_score}</text>
  <rect x="534" y="340" width="174" height="112" rx="24" fill="#fffaf4" stroke="#1f2630" stroke-opacity="0.12"/>
  <text x="558" y="382" font-size="16" font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" fill="#7b7268">Findings</text>
  <text x="558" y="432" font-size="42" font-weight="800" font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" fill="#1f2630">{int(report.get("proven_findings_count", 0))}</text>
  <text x="56" y="560" font-size="24" font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" fill="#5f666e">Prompt injection evidence page for healthcare AI workflows</text>
</svg>
"""


def write_share_bundle(report: dict, outdir: str, *, source_label: str, title: str | None) -> dict:
    bundle_dir = Path(outdir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    bundle_title = title or "Honeypot Med Threat Snapshot"
    bundle_manifest = build_bundle_manifest(report, title=bundle_title, source_label=source_label)
    bundle_path = bundle_dir / "bundle.json"
    json_path = bundle_dir / "report.json"
    markdown_path = bundle_dir / "report.md"
    html_path = bundle_dir / "index.html"
    social_path = bundle_dir / "social-card.svg"
    pdf_path = bundle_dir / "summary.pdf"

    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    markdown_lines = [
        "# Honeypot Med Report",
        "",
        f"- Total events: {report.get('total_prompts', 0)}",
        f"- High risk events: {report.get('high_risk_count', 0)}",
        f"- Hypotheses: {report.get('hypotheses_count', 0)}",
        f"- Proven findings: {report.get('proven_findings_count', 0)}",
        f"- Suppressed findings: {report.get('suppressed_finding_count', 0)}",
        "",
        "| Prompt | Severity | Risk | Findings | Proven |",
        "|---|---|---:|---:|---:|",
    ]
    for event in report.get("events", []):
        prompt = str(event.get("prompt", "")).replace("|", "\\|")
        if len(prompt) > 80:
            prompt = prompt[:77] + "..."
        markdown_lines.append(
            "| {prompt} | {severity} | {risk} | {findings} | {proven} |".format(
                prompt=prompt,
                severity=event.get("severity", "low"),
                risk=event.get("risk_score", 0),
                findings=event.get("finding_count", 0),
                proven=event.get("proven_count", 0),
            )
        )
    markdown_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")

    html_path.write_text(
        build_share_html(report, source_label=source_label, title=bundle_title) + "\n",
        encoding="utf-8",
    )
    social_path.write_text(
        build_social_card_svg(report, title=bundle_title, source_label=source_label) + "\n",
        encoding="utf-8",
    )
    pdf_path.write_bytes(_build_summary_pdf(report, title=bundle_title, source_label=source_label))
    bundle_manifest["artifacts"] = {
        "bundle": bundle_path.name,
        "html": html_path.name,
        "json": json_path.name,
        "markdown": markdown_path.name,
        "social_card": social_path.name,
        "pdf": pdf_path.name,
    }
    bundle_path.write_text(json.dumps(bundle_manifest, indent=2) + "\n", encoding="utf-8")

    return {
        "status": "created",
        "outdir": str(bundle_dir),
        "bundle_manifest_path": str(bundle_path),
        "html_path": str(html_path),
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
        "social_card_path": str(social_path),
        "pdf_path": str(pdf_path),
    }
