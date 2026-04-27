"""Export builders for share bundles, social cards, and PDF summaries."""

from __future__ import annotations

import json
import textwrap
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from .branding import load_default_hero_data_uri
from .casebook import write_casebook_artifacts
from .eval_adapters import write_eval_adapter_artifacts
from .github_summary import write_github_summary
from .junit import write_junit_xml
from .launchkit import build_launch_json, build_launch_kit, build_launch_markdown, bundle_verdict
from .lab import write_lab_artifacts
from .observability import write_observability_artifacts
from .outputs.badge import build_badge_markdown, build_report_badge_svg
from .outputs.otel import report_to_otel_logs
from .outputs.sarif import report_to_sarif
from .png_cards import write_png_card_artifacts
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
    pdf.extend(b"0000000000 65535 f\n")
    for obj_id in range(1, max(ordered_ids) + 1):
        offset = offsets.get(obj_id, 0)
        pdf.extend(f"{offset:010d} 00000 n\n".encode("latin-1"))
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
        "verdict": bundle_verdict(report),
        "prompts_analyzed": int(report.get("total_prompts", 0)),
        "high_risk_count": int(report.get("high_risk_count", 0)),
        "proven_findings_count": int(report.get("proven_findings_count", 0)),
        "top_risk_score": int(top_event.get("risk_score", 0)),
        "prompt_excerpt": prompt_excerpt,
    }


def build_social_card_svg(report: dict, *, title: str, source_label: str) -> str:
    hero = load_default_hero_data_uri()
    verdict = bundle_verdict(report)
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
    badge_path = bundle_dir / "badge.svg"
    badge_markdown_path = bundle_dir / "README-badge.md"
    pdf_path = bundle_dir / "summary.pdf"
    launch_markdown_path = bundle_dir / "launch-kit.md"
    launch_json_path = bundle_dir / "launch-kit.json"
    sarif_path = bundle_dir / "honeypot-med.sarif"
    otel_path = bundle_dir / "otel-logs.json"
    junit_path = bundle_dir / "honeypot-med.junit.xml"
    github_summary_path = bundle_dir / "github-summary.md"

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
    launch_kit = build_launch_kit(report, title=bundle_title, source_label=source_label)
    launch_markdown_path.write_text(build_launch_markdown(launch_kit), encoding="utf-8")
    launch_json_path.write_text(build_launch_json(launch_kit), encoding="utf-8")

    html_path.write_text(
        build_share_html(report, source_label=source_label, title=bundle_title).rstrip() + "\n",
        encoding="utf-8",
    )
    social_path.write_text(
        build_social_card_svg(report, title=bundle_title, source_label=source_label).rstrip() + "\n",
        encoding="utf-8",
    )
    badge_path.write_text(build_report_badge_svg(report), encoding="utf-8")
    badge_markdown_path.write_text(
        build_badge_markdown(report_url="index.html", badge_path=badge_path.name),
        encoding="utf-8",
    )
    pdf_path.write_bytes(_build_summary_pdf(report, title=bundle_title, source_label=source_label))
    png_artifacts = write_png_card_artifacts(report, str(bundle_dir), title=bundle_title, source_label=source_label)
    sarif_path.write_text(
        json.dumps(report_to_sarif(report, source_label=source_label), indent=2) + "\n",
        encoding="utf-8",
    )
    otel_path.write_text(
        json.dumps(report_to_otel_logs(report, source_label=source_label), indent=2) + "\n",
        encoding="utf-8",
    )
    write_junit_xml(report, str(junit_path), suite_name=bundle_title, source_label=source_label)
    write_github_summary(report, str(github_summary_path), title=bundle_title, source_label=source_label)
    lab_artifacts = write_lab_artifacts(
        report,
        str(bundle_dir),
        source_label=source_label,
        title=bundle_title,
    )
    eval_artifacts = write_eval_adapter_artifacts(
        report,
        str(bundle_dir),
        source_label=source_label,
        title=bundle_title,
    )
    casebook_artifacts = write_casebook_artifacts(
        report,
        str(bundle_dir),
        source_label=source_label,
        title=bundle_title,
    )
    observability_artifacts = write_observability_artifacts(
        report,
        str(bundle_dir),
        source_label=source_label,
    )
    bundle_manifest["artifacts"] = {
        "bundle": bundle_path.name,
        "html": html_path.name,
        "json": json_path.name,
        "markdown": markdown_path.name,
        "social_card": social_path.name,
        "social_card_png": Path(png_artifacts["social_card_png"]).name,
        "badge": badge_path.name,
        "badge_png": Path(png_artifacts["badge_png"]).name,
        "badge_markdown": badge_markdown_path.name,
        "pdf": pdf_path.name,
        "launch_markdown": launch_markdown_path.name,
        "launch_json": launch_json_path.name,
        "sarif": sarif_path.name,
        "otel_logs": otel_path.name,
        "junit": junit_path.name,
        "github_summary": github_summary_path.name,
        "specimen_codex": Path(lab_artifacts["specimen_codex"]).name,
        "trap_ledger_json": Path(lab_artifacts["trap_ledger_json"]).name,
        "trap_ledger_csv": Path(lab_artifacts["trap_ledger_csv"]).name,
        "field_guide": Path(lab_artifacts["field_guide"]).name,
        "offline_proof": Path(lab_artifacts["offline_proof"]).name,
        "proof_dossier_html": Path(lab_artifacts["proof_dossier_html"]).name,
        "proof_dossier_pdf": Path(lab_artifacts["proof_dossier_pdf"]).name,
        "ui_mockup": Path(lab_artifacts["ui_mockup"]).name,
        "research_questions": Path(lab_artifacts["research_questions"]).name,
        "inquiry_notebook": Path(lab_artifacts["inquiry_notebook"]).name,
        "unknown_ledger": Path(lab_artifacts["unknown_ledger"]).name,
        "counterfactual_prompts": Path(lab_artifacts["counterfactual_prompts"]).name,
        "experiment_matrix": Path(lab_artifacts["experiment_matrix"]).name,
        "question_atlas": Path(lab_artifacts["question_atlas"]).name,
        "experiment_plan": Path(lab_artifacts["experiment_plan"]).name,
        "ablation_ladder": Path(lab_artifacts["ablation_ladder"]).name,
        "eval_samples": Path(eval_artifacts["eval_samples"]).name,
        "inspect_dataset": Path(eval_artifacts["inspect_dataset"]).name,
        "promptfoo_config": Path(eval_artifacts["promptfoo_config"]).name,
        "promptfoo_tests": Path(eval_artifacts["promptfoo_tests"]).name,
        "openai_evals_yaml": Path(eval_artifacts["openai_evals_yaml"]).name,
        "openai_evals_samples": Path(eval_artifacts["openai_evals_samples"]).name,
        "eval_kit": Path(eval_artifacts["eval_kit"]).name,
        "eval_kit_manifest": Path(eval_artifacts["eval_kit_manifest"]).name,
        "hf_dataset_card": Path(eval_artifacts["hf_dataset_card"]).name,
        "hf_system_card": Path(eval_artifacts["hf_system_card"]).name,
        "hf_artifact_manifest": Path(eval_artifacts["hf_artifact_manifest"]).name,
        "casebook_json": Path(casebook_artifacts["casebook_json"]).name,
        "casebook_html": Path(casebook_artifacts["casebook_html"]).name,
        "casebook_xray_html": Path(casebook_artifacts["casebook_xray_html"]).name,
        "casebook_ledger_html": Path(casebook_artifacts["casebook_ledger_html"]).name,
        "traparium_html": Path(casebook_artifacts["traparium_html"]).name,
        "unknowns_html": Path(casebook_artifacts["unknowns_html"]).name,
        "failure_recipes": Path(casebook_artifacts["failure_recipes"]).name,
        "trap_tree": Path(casebook_artifacts["trap_tree"]).name,
        "lab_notebook": Path(casebook_artifacts["lab_notebook"]).name,
        "openinference_traces": Path(observability_artifacts["openinference_traces"]).name,
        "langsmith_runs": Path(observability_artifacts["langsmith_runs"]).name,
        "otel_collector_config": Path(observability_artifacts["otel_collector_config"]).name,
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
        "social_card_png_path": png_artifacts["social_card_png"],
        "badge_path": str(badge_path),
        "badge_png_path": png_artifacts["badge_png"],
        "badge_markdown_path": str(badge_markdown_path),
        "pdf_path": str(pdf_path),
        "launch_markdown_path": str(launch_markdown_path),
        "launch_json_path": str(launch_json_path),
        "sarif_path": str(sarif_path),
        "otel_logs_path": str(otel_path),
        "junit_path": str(junit_path),
        "github_summary_path": str(github_summary_path),
        "specimen_codex_path": lab_artifacts["specimen_codex"],
        "trap_ledger_json_path": lab_artifacts["trap_ledger_json"],
        "trap_ledger_csv_path": lab_artifacts["trap_ledger_csv"],
        "field_guide_path": lab_artifacts["field_guide"],
        "offline_proof_path": lab_artifacts["offline_proof"],
        "proof_dossier_html_path": lab_artifacts["proof_dossier_html"],
        "proof_dossier_pdf_path": lab_artifacts["proof_dossier_pdf"],
        "ui_mockup_path": lab_artifacts["ui_mockup"],
        "research_questions_path": lab_artifacts["research_questions"],
        "inquiry_notebook_path": lab_artifacts["inquiry_notebook"],
        "unknown_ledger_path": lab_artifacts["unknown_ledger"],
        "counterfactual_prompts_path": lab_artifacts["counterfactual_prompts"],
        "experiment_matrix_path": lab_artifacts["experiment_matrix"],
        "question_atlas_path": lab_artifacts["question_atlas"],
        "experiment_plan_path": lab_artifacts["experiment_plan"],
        "ablation_ladder_path": lab_artifacts["ablation_ladder"],
        "eval_samples_path": eval_artifacts["eval_samples"],
        "inspect_dataset_path": eval_artifacts["inspect_dataset"],
        "promptfoo_config_path": eval_artifacts["promptfoo_config"],
        "promptfoo_tests_path": eval_artifacts["promptfoo_tests"],
        "openai_evals_yaml_path": eval_artifacts["openai_evals_yaml"],
        "openai_evals_samples_path": eval_artifacts["openai_evals_samples"],
        "eval_kit_path": eval_artifacts["eval_kit"],
        "eval_kit_manifest_path": eval_artifacts["eval_kit_manifest"],
        "hf_dataset_card_path": eval_artifacts["hf_dataset_card"],
        "hf_system_card_path": eval_artifacts["hf_system_card"],
        "hf_artifact_manifest_path": eval_artifacts["hf_artifact_manifest"],
        "casebook_json_path": casebook_artifacts["casebook_json"],
        "casebook_html_path": casebook_artifacts["casebook_html"],
        "casebook_xray_html_path": casebook_artifacts["casebook_xray_html"],
        "casebook_ledger_html_path": casebook_artifacts["casebook_ledger_html"],
        "traparium_html_path": casebook_artifacts["traparium_html"],
        "unknowns_html_path": casebook_artifacts["unknowns_html"],
        "failure_recipes_path": casebook_artifacts["failure_recipes"],
        "trap_tree_path": casebook_artifacts["trap_tree"],
        "lab_notebook_path": casebook_artifacts["lab_notebook"],
        "openinference_traces_path": observability_artifacts["openinference_traces"],
        "langsmith_runs_path": observability_artifacts["langsmith_runs"],
        "otel_collector_config_path": observability_artifacts["otel_collector_config"],
    }
