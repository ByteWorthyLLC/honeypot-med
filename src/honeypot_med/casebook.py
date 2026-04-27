"""Casebook artifacts for turning scan output into a local research object."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from .inquiry import build_question_bank
from .redaction import redact_text
from .specimens import build_specimen_codex


def _short(value: object, limit: int = 180) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _redacted_short(value: object, limit: int = 180) -> str:
    redacted, _ = redact_text(str(value or ""))
    return _short(redacted, limit)


def _families(event: dict) -> list[str]:
    seen: dict[str, None] = {}
    for finding in event.get("findings", []):
        seen[str(finding.get("attack_family", "unknown"))] = None
    return list(seen)


def _survived(event: dict) -> bool:
    severity = str(event.get("severity", "low")).lower()
    return int(event.get("proven_count", 0)) == 0 and severity not in {"high", "critical"}


def _event_fingerprint(event: dict, index: int) -> str:
    payload = json.dumps(
        {
            "index": index,
            "prompt": str(event.get("prompt", "")),
            "findings": event.get("findings", []),
            "tool_calls": event.get("tool_calls", []),
        },
        sort_keys=True,
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def _status(event: dict) -> str:
    if _survived(event):
        return "survived"
    if int(event.get("proven_count", 0)) > 0:
        return "bitten"
    return "uncertain"


def build_casebook(report: dict, *, source_label: str, title: str) -> dict:
    """Build a compact, redacted forensic casebook for HTML/JSON output."""
    events = []
    for index, event in enumerate(report.get("events", []), start=1):
        findings = []
        for finding_index, finding in enumerate(event.get("findings", []), start=1):
            findings.append(
                {
                    "id": f"trap-{index:03d}-finding-{finding_index:02d}",
                    "rule_id": str(finding.get("rule_id", "UNKNOWN")),
                    "attack_family": str(finding.get("attack_family", "unknown")),
                    "severity": str(finding.get("severity", event.get("severity", "low"))),
                    "score": int(finding.get("score", 0)),
                    "proven": bool(finding.get("proven")),
                    "evidence": [_redacted_short(item, 140) for item in finding.get("evidence", [])],
                }
            )
        tool_calls = []
        for tool in event.get("tool_calls", []):
            if not isinstance(tool, dict):
                continue
            tool_calls.append(
                {
                    "name": str(tool.get("name", "")),
                    "args_excerpt": _redacted_short(tool.get("args", ""), 140),
                }
            )

        events.append(
            {
                "id": f"trap-{index:03d}",
                "fingerprint": _event_fingerprint(event, index),
                "status": _status(event),
                "severity": str(event.get("severity", "low")),
                "risk_score": int(event.get("risk_score", 0)),
                "families": _families(event) or ["unknown"],
                "prompt_excerpt": _redacted_short(event.get("prompt", ""), 220),
                "model_output_excerpt": _redacted_short(event.get("model_output", ""), 180),
                "response_excerpt": _redacted_short(event.get("response", ""), 180),
                "tool_calls": tool_calls,
                "findings": findings,
                "questions": [
                    "What evidence would falsify this finding?",
                    "Which tool capability made this prompt dangerous?",
                    "What is the smallest safe version of the same user intent?",
                ],
            }
        )

    survived = sum(1 for event in events if event["status"] == "survived")
    bitten = sum(1 for event in events if event["status"] == "bitten")
    uncertain = len(events) - survived - bitten
    return {
        "title": title,
        "source_label": source_label,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stance": "research instrument, not scanner",
        "summary": {
            "events": len(events),
            "survived": survived,
            "bitten": bitten,
            "uncertain": uncertain,
            "high_risk_events": int(report.get("high_risk_count", 0)),
            "proven_findings": int(report.get("proven_findings_count", 0)),
        },
        "events": events,
        "specimens": build_specimen_codex(report)["specimens"],
        "unknowns": build_question_bank(report, source_label=source_label)["unknowns"],
    }


def _html_shell(*, title: str, body: str, subtitle: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(title)}</title>
  <style>
    :root {{
      --bg: #181712;
      --paper: #f5ead6;
      --card: #fff8ea;
      --ink: #211d17;
      --muted: #6f6252;
      --line: rgba(33, 29, 23, 0.16);
      --accent: #bc432c;
      --green: #23745b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 15% 8%, rgba(188, 67, 44, 0.28), transparent 26rem),
        radial-gradient(circle at 85% 0%, rgba(35, 116, 91, 0.24), transparent 24rem),
        linear-gradient(135deg, #1d1a14, #463522 58%, #1b201b);
      font-family: Avenir Next, Helvetica Neue, Arial, sans-serif;
    }}
    .wrap {{ width: min(1120px, calc(100vw - 32px)); margin: 0 auto; padding: 36px 0; }}
    header {{ color: var(--paper); margin-bottom: 20px; }}
    .kicker {{ letter-spacing: .18em; text-transform: uppercase; font-size: 12px; color: #dec7a5; }}
    h1 {{ font-family: Iowan Old Style, Palatino Linotype, Georgia, serif; font-size: clamp(2.4rem, 6vw, 5.2rem); line-height: .95; margin: 12px 0; letter-spacing: -.05em; }}
    .subtitle {{ max-width: 760px; color: #ebdcc4; font-size: 18px; line-height: 1.6; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }}
    .card, .specimen, .unknown, .recipe {{ background: rgba(255, 248, 234, .95); border: 1px solid var(--line); border-radius: 24px; padding: 18px; box-shadow: 0 20px 70px rgba(0,0,0,.18); }}
    .card h2, .specimen h2, .unknown h2, .recipe h2 {{ margin: 0 0 8px; font-size: 18px; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }}
    .pill {{ border: 1px solid var(--line); border-radius: 999px; padding: 5px 9px; font-size: 12px; color: var(--muted); background: rgba(255,255,255,.42); }}
    .status-survived {{ color: var(--green); font-weight: 800; }}
    .status-bitten {{ color: var(--accent); font-weight: 800; }}
    .status-uncertain {{ color: #8b6423; font-weight: 800; }}
    pre {{ white-space: pre-wrap; background: #211d17; color: #f7ebd5; border-radius: 16px; padding: 12px; overflow: auto; }}
    ul {{ padding-left: 20px; }}
    a {{ color: inherit; }}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <div class="kicker">Honeypot Med Casebook</div>
      <h1>{escape(title)}</h1>
      <p class="subtitle">{escape(subtitle)}</p>
    </header>
    {body}
  </div>
</body>
</html>
"""


def build_casebook_html(casebook: dict) -> str:
    cards = []
    for event in casebook["events"]:
        findings = "".join(
            f"<li><strong>{escape(item['rule_id'])}</strong> {escape(item['attack_family'])} "
            f"score {int(item['score'])} proven={str(bool(item['proven'])).lower()}</li>"
            for item in event["findings"]
        ) or "<li>No findings. Treat as a quiet object worth retesting.</li>"
        tools = "".join(
            f"<li>{escape(tool['name'])}: {escape(tool['args_excerpt'])}</li>"
            for tool in event["tool_calls"]
        ) or "<li>No tool calls observed.</li>"
        questions = "".join(f"<li>{escape(question)}</li>" for question in event["questions"])
        status = str(event["status"])
        cards.append(
            f"""<article class="card">
  <h2>{escape(event['id'])} <span class="status-{escape(status)}">{escape(status)}</span></h2>
  <div class="meta">
    <span class="pill">risk {int(event['risk_score'])}</span>
    <span class="pill">{escape(event['severity'])}</span>
    <span class="pill">{escape(', '.join(event['families']))}</span>
    <span class="pill">fp {escape(event['fingerprint'])}</span>
  </div>
  <pre>{escape(event['prompt_excerpt'])}</pre>
  <h3>Tool reach</h3>
  <ul>{tools}</ul>
  <h3>Findings</h3>
  <ul>{findings}</ul>
  <h3>Next questions</h3>
  <ul>{questions}</ul>
</article>"""
        )
    body = f"<section class=\"grid\">{''.join(cards)}</section>"
    return _html_shell(
        title=str(casebook["title"]) + " Casebook",
        subtitle="A redacted forensic notebook: prompts, tool reach, findings, unknowns, and falsification questions.",
        body=body,
    )


def build_traparium_html(casebook: dict) -> str:
    cards = []
    for specimen in casebook["specimens"]:
        cards.append(
            f"""<article class="specimen">
  <h2>{escape(specimen['name'])}</h2>
  <div class="meta">
    <span class="pill">{escape(specimen['attack_family'])}</span>
    <span class="pill">sightings {int(specimen['sightings'])}</span>
    <span class="pill">bites {int(specimen['proven_sightings'])}</span>
  </div>
  <p>{escape(specimen['temperament'])}</p>
  <p><strong>Tells:</strong> {escape(', '.join(specimen['tells']))}</p>
  <p><strong>Containment:</strong> {escape(specimen['containment'])}</p>
</article>"""
        )
    return _html_shell(
        title=str(casebook["title"]) + " Traparium",
        subtitle="A museum cabinet for failure modes. Every bland finding gets a specimen label.",
        body=f"<section class=\"grid\">{''.join(cards)}</section>",
    )


def build_unknowns_html(casebook: dict) -> str:
    rows = []
    for unknown in casebook["unknowns"]:
        rows.append(
            f"""<article class="unknown">
  <h2>Event {int(unknown['event'])}: {escape(unknown['unknown'])}</h2>
  <p>{escape(unknown['question'])}</p>
  <pre>{escape(str(unknown['prompt_excerpt']))}</pre>
</article>"""
        )
    if not rows:
        rows.append(
            """<article class="unknown"><h2>No unknowns recorded</h2><p>This run produced either clear findings or clear passes. Rerun with a narrower pack if that feels suspicious.</p></article>"""
        )
    return _html_shell(
        title=str(casebook["title"]) + " Unknowns",
        subtitle="A playable ledger for ambiguity: quiet passes, unproven hypotheses, and missing telemetry.",
        body=f"<section class=\"grid\">{''.join(rows)}</section>",
    )


def build_failure_recipes_markdown(casebook: dict) -> str:
    lines = [
        f"# {casebook['title']} Failure Recipes",
        "",
        "Use these as local retest recipes. Change one variable at a time.",
        "",
    ]
    for specimen in casebook["specimens"]:
        lines.extend(
            [
                f"## {specimen['name']}",
                "",
                f"- Family: `{specimen['attack_family']}`",
                f"- Symptom: {specimen['temperament']}",
                f"- Tells: {', '.join(specimen['tells'])}",
                f"- Containment recipe: {specimen['containment']}",
                "- Retest: rerun the same prompt with no tools, read-only tools, export tools, then admin tools.",
                "",
            ]
        )
    return "\n".join(lines)


def build_trap_tree_svg(casebook: dict) -> str:
    width = 980
    height = max(360, 120 + len(casebook["events"]) * 58)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
        '<rect width="100%" height="100%" fill="#f5ead6"/>',
        '<text x="36" y="50" font-size="28" font-weight="800" font-family="Avenir Next, Arial" fill="#211d17">Trap Phylogeny</text>',
        '<text x="36" y="78" font-size="14" font-family="Avenir Next, Arial" fill="#6f6252">Specimen families linked to observed traps</text>',
    ]
    family_y: dict[str, int] = {}
    for index, specimen in enumerate(casebook["specimens"], start=1):
        y = 120 + (index - 1) * 74
        family_y[str(specimen["attack_family"])] = y
        lines.extend(
            [
                f'<rect x="36" y="{y - 28}" width="280" height="46" rx="16" fill="#fff8ea" stroke="#d6c3a3"/>',
                f'<text x="54" y="{y}" font-size="15" font-weight="800" font-family="Avenir Next, Arial" fill="#211d17">{escape(specimen["name"])}</text>',
            ]
        )
    for index, event in enumerate(casebook["events"], start=1):
        y = 120 + (index - 1) * 58
        color = {"survived": "#23745b", "bitten": "#bc432c"}.get(str(event["status"]), "#8b6423")
        lines.extend(
            [
                f'<circle cx="760" cy="{y}" r="18" fill="{color}"/>',
                f'<text x="790" y="{y + 5}" font-size="14" font-family="Avenir Next, Arial" fill="#211d17">{escape(event["id"])} {escape(event["status"])}</text>',
            ]
        )
        for family in event["families"]:
            start_y = family_y.get(str(family), 120)
            lines.append(
                f'<path d="M316 {start_y} C460 {start_y}, 560 {y}, 742 {y}" fill="none" stroke="#6f6252" stroke-opacity=".45" stroke-width="2"/>'
            )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def build_lab_notebook_ipynb(casebook: dict) -> dict:
    """Return a tiny Jupyter notebook that keeps investigation reproducible."""
    summary = json.dumps(casebook["summary"], indent=2)
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# {casebook['title']} Lab Notebook\n",
                    "\n",
                    "Generated by Honeypot Med. No model API calls are required.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["summary = ", summary, "\nsummary\n"],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Next experiment\n",
                    "\n",
                    "Pick one event, change one variable, rerun `python app.py casebook --input ...`.\n",
                ],
            },
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write_casebook_artifacts(report: dict, outdir: str, *, source_label: str, title: str) -> dict:
    target = Path(outdir)
    target.mkdir(parents=True, exist_ok=True)
    casebook = build_casebook(report, source_label=source_label, title=title)

    casebook_json_path = target / "casebook.json"
    casebook_html_path = target / "casebook.html"
    traparium_path = target / "traparium.html"
    unknowns_path = target / "unknowns.html"
    recipes_path = target / "failure-recipes.md"
    tree_path = target / "trap-tree.svg"
    notebook_path = target / "lab-notebook.ipynb"

    casebook_json_path.write_text(json.dumps(casebook, indent=2) + "\n", encoding="utf-8")
    casebook_html_path.write_text(build_casebook_html(casebook), encoding="utf-8")
    traparium_path.write_text(build_traparium_html(casebook), encoding="utf-8")
    unknowns_path.write_text(build_unknowns_html(casebook), encoding="utf-8")
    recipes_path.write_text(build_failure_recipes_markdown(casebook), encoding="utf-8")
    tree_path.write_text(build_trap_tree_svg(casebook), encoding="utf-8")
    notebook_path.write_text(json.dumps(build_lab_notebook_ipynb(casebook), indent=2) + "\n", encoding="utf-8")

    return {
        "casebook_json": str(casebook_json_path),
        "casebook_html": str(casebook_html_path),
        "traparium_html": str(traparium_path),
        "unknowns_html": str(unknowns_path),
        "failure_recipes": str(recipes_path),
        "trap_tree": str(tree_path),
        "lab_notebook": str(notebook_path),
    }
