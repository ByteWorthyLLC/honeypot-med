"""Diff two casebooks for local evidence review."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path


def _load_casebook(path: str) -> dict:
    candidate = Path(path)
    if candidate.is_dir():
        candidate = candidate / "casebook.json"
    raw = json.loads(candidate.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "events" not in raw:
        raise ValueError(f"{candidate} is not a casebook JSON file")
    return raw


def _event_key(event: dict) -> str:
    return str(event.get("fingerprint") or event.get("id") or event.get("prompt_excerpt", ""))


def build_casebook_diff(base: dict, target: dict) -> dict:
    base_events = {_event_key(event): event for event in base.get("events", [])}
    target_events = {_event_key(event): event for event in target.get("events", [])}
    added = sorted(set(target_events) - set(base_events))
    removed = sorted(set(base_events) - set(target_events))
    changed = []
    for key in sorted(set(base_events) & set(target_events)):
        left = base_events[key]
        right = target_events[key]
        risk_delta = int(right.get("risk_score", 0)) - int(left.get("risk_score", 0))
        status_changed = str(left.get("status")) != str(right.get("status"))
        families_changed = list(left.get("families", [])) != list(right.get("families", []))
        findings_delta = len(right.get("findings", [])) - len(left.get("findings", []))
        if risk_delta or status_changed or families_changed or findings_delta:
            changed.append(
                {
                    "key": key,
                    "base_id": str(left.get("id", "")),
                    "target_id": str(right.get("id", "")),
                    "base_status": str(left.get("status", "")),
                    "target_status": str(right.get("status", "")),
                    "risk_delta": risk_delta,
                    "findings_delta": findings_delta,
                    "base_families": list(left.get("families", [])),
                    "target_families": list(right.get("families", [])),
                    "prompt_excerpt": str(right.get("prompt_excerpt") or left.get("prompt_excerpt") or ""),
                }
            )
    return {
        "base_title": str(base.get("title", "base")),
        "target_title": str(target.get("title", "target")),
        "summary": {
            "added": len(added),
            "removed": len(removed),
            "changed": len(changed),
            "base_events": len(base_events),
            "target_events": len(target_events),
        },
        "added": [target_events[key] for key in added],
        "removed": [base_events[key] for key in removed],
        "changed": changed,
    }


def build_casebook_diff_markdown(diff: dict) -> str:
    lines = [
        "# Honeypot Med Casebook Diff",
        "",
        f"- Base: {diff['base_title']}",
        f"- Target: {diff['target_title']}",
        f"- Added traps: {diff['summary']['added']}",
        f"- Removed traps: {diff['summary']['removed']}",
        f"- Changed traps: {diff['summary']['changed']}",
        "",
        "## Changed Traps",
        "",
        "| Trap | Status | Risk Delta | Findings Delta | Families | Prompt |",
        "|---|---|---:|---:|---|---|",
    ]
    for item in diff["changed"]:
        prompt = str(item["prompt_excerpt"]).replace("|", "\\|")
        lines.append(
            "| {trap} | {base} -> {target} | {risk} | {findings} | {families} | {prompt} |".format(
                trap=item["target_id"] or item["base_id"],
                base=item["base_status"],
                target=item["target_status"],
                risk=item["risk_delta"],
                findings=item["findings_delta"],
                families=", ".join(item["target_families"]),
                prompt=prompt[:160],
            )
        )
    if not diff["changed"]:
        lines.append("| none | stable | 0 | 0 | none | no changes |")
    lines.append("")
    return "\n".join(lines)


def build_casebook_diff_html(diff: dict) -> str:
    cards = []
    for item in diff["changed"]:
        cards.append(
            f"""<article>
  <h2>{escape(item['target_id'] or item['base_id'])}</h2>
  <p><strong>Status:</strong> {escape(item['base_status'])} -> {escape(item['target_status'])}</p>
  <p><strong>Risk delta:</strong> {int(item['risk_delta'])}</p>
  <p><strong>Findings delta:</strong> {int(item['findings_delta'])}</p>
  <p><strong>Families:</strong> {escape(', '.join(item['target_families']))}</p>
  <pre>{escape(str(item['prompt_excerpt']))}</pre>
</article>"""
        )
    if not cards:
        cards.append("<article><h2>No changed traps</h2><p>The compared casebooks are stable on matched fingerprints.</p></article>")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Honeypot Med Casebook Diff</title>
  <style>
    body {{ margin: 0; background: #171812; color: #f8ead1; font-family: Avenir Next, Arial, sans-serif; }}
    main {{ width: min(1080px, calc(100vw - 32px)); margin: 0 auto; padding: 36px 0; }}
    h1 {{ font-family: Iowan Old Style, Georgia, serif; font-size: clamp(2.4rem, 7vw, 5rem); line-height: .95; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }}
    article {{ border: 1px solid rgba(248,234,209,.18); background: rgba(248,234,209,.08); border-radius: 22px; padding: 18px; }}
    pre {{ white-space: pre-wrap; color: #211d17; background: #fff8ea; border-radius: 16px; padding: 12px; }}
  </style>
</head>
<body>
  <main>
    <h1>Casebook Diff</h1>
    <p>{escape(diff['base_title'])} -> {escape(diff['target_title'])}</p>
    <p>Added {diff['summary']['added']}. Removed {diff['summary']['removed']}. Changed {diff['summary']['changed']}.</p>
    <section class="grid">{''.join(cards)}</section>
  </main>
</body>
</html>
"""


def write_casebook_diff_artifacts(base_path: str, target_path: str, outdir: str) -> dict:
    target = Path(outdir)
    target.mkdir(parents=True, exist_ok=True)
    diff = build_casebook_diff(_load_casebook(base_path), _load_casebook(target_path))
    json_path = target / "casebook-diff.json"
    md_path = target / "casebook-diff.md"
    html_path = target / "casebook-diff.html"
    json_path.write_text(json.dumps(diff, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(build_casebook_diff_markdown(diff), encoding="utf-8")
    html_path.write_text(build_casebook_diff_html(diff), encoding="utf-8")
    return {
        "casebook_diff_json": str(json_path),
        "casebook_diff_markdown": str(md_path),
        "casebook_diff_html": str(html_path),
    }
