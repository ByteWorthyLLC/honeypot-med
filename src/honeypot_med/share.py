"""Standalone share-page rendering for Honeypot Med reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape

from .branding import load_default_hero_data_uri
from .launchkit import build_launch_kit
from .specimens import build_specimen_codex


def _verdict(report: dict) -> tuple[str, str]:
    severity = report.get("severity_counts", {})
    if int(severity.get("critical", 0)) > 0 or int(severity.get("high", 0)) > 0:
        return "BLOCK", "This workflow showed evidence-backed exploit behavior."
    if int(severity.get("medium", 0)) > 0:
        return "REVIEW", "This workflow triggered suspicious prompt-injection patterns."
    return "PASS", "This workflow stayed within safe operating bounds."


def _score_band(score: int) -> str:
    if score >= 85:
        return "Critical"
    if score >= 60:
        return "High"
    if score >= 35:
        return "Medium"
    return "Low"


def _metric(label: str, value: str) -> str:
    return (
        '<div class="metric">'
        f'<div class="metric-value">{escape(value)}</div>'
        f'<div class="metric-label">{escape(label)}</div>'
        "</div>"
    )


def _copy_card(label: str, value: str) -> str:
    safe_value = escape(value)
    attr_value = safe_value.replace("\n", "&#10;")
    return (
        '<article class="copy-card">'
        f"<h3>{escape(label)}</h3>"
        f'<p>{safe_value}</p>'
        '<button class="copy-button" type="button" data-copy="'
        f"{attr_value}"
        '">Copy</button>'
        "</article>"
    )


def _finding_markup(finding: dict) -> str:
    evidence = finding.get("evidence", [])
    evidence_markup = "".join(
        f'<li>{escape(str(item))}</li>' for item in evidence
    ) or "<li>No proof signals captured yet.</li>"

    return (
        '<article class="finding">'
        f'<div class="finding-topline">{escape(str(finding.get("attack_family", "unknown")).replace("_", " "))}</div>'
        f'<h4>{escape(str(finding.get("rule_id", "UNKNOWN")))}: {escape(str(finding.get("hit", "")))}</h4>'
        '<div class="finding-meta">'
        f'<span>{escape(_score_band(int(finding.get("score", 0))))} risk</span>'
        f'<span>{"Proven" if finding.get("proven") else "Hypothesis"}</span>'
        "</div>"
        '<ul class="evidence-list">'
        f"{evidence_markup}"
        "</ul>"
        "</article>"
    )


def _event_markup(event: dict) -> str:
    findings = event.get("findings", [])
    finding_markup = "".join(_finding_markup(finding) for finding in findings)
    if not finding_markup:
        finding_markup = '<div class="empty-state">No findings detected.</div>'

    return (
        '<section class="event-card">'
        '<div class="event-header">'
        f'<div class="severity-pill severity-{escape(str(event.get("severity", "low")))}">{escape(str(event.get("severity", "low")).upper())}</div>'
        f'<div class="event-score">{int(event.get("risk_score", 0))}</div>'
        "</div>"
        f'<h3>{escape(str(event.get("prompt", "")))}</h3>'
        '<div class="event-meta">'
        f'<span>{int(event.get("tool_call_count", 0))} tool calls</span>'
        f'<span>{int(event.get("finding_count", 0))} findings</span>'
        f'<span>{int(event.get("proven_count", 0))} proven</span>'
        "</div>"
        f'<div class="finding-grid">{finding_markup}</div>'
        "</section>"
    )


def _challenge_markup(challenge: object) -> str:
    if not isinstance(challenge, dict):
        return ""

    baseline_markup = ""
    for baseline in challenge.get("baselines", []):
        if not isinstance(baseline, dict):
            continue
        delta = int(baseline.get("delta", 0))
        delta_label = f"+{delta}" if delta > 0 else str(delta)
        baseline_markup += (
            '<article class="baseline-card">'
            f'<div class="baseline-topline">{escape(str(baseline.get("label", "")))}</div>'
            f'<strong>{int(baseline.get("survived", 0))}/{int(baseline.get("total", 10))} survived</strong>'
            f'<span>{escape(delta_label)} vs this run</span>'
            f'<p>{escape(str(baseline.get("notes", "")))}</p>'
            "</article>"
        )

    return (
        '<section class="challenge-panel panel">'
        '<div class="challenge-copy">'
        '<div class="eyebrow">Challenge Mode</div>'
        f'<h2>{escape(str(challenge.get("question", "Can your healthcare AI survive the traps?")))}</h2>'
        f'<p>This run scored <strong>{escape(str(challenge.get("score_label", "0/0 survived")))}</strong> with a {escape(str(challenge.get("verdict", "review")).replace("-", " "))} verdict. Use the badge artifact in a README, launch post, or release note.</p>'
        '</div>'
        '<div class="challenge-score">'
        f'<strong>{escape(str(challenge.get("score_label", "0/0 survived")))}</strong>'
        f'<span>{int(challenge.get("score_percent", 0))}% trap survival</span>'
        '</div>'
        f'<div class="baseline-grid">{baseline_markup}</div>'
        "</section>"
    )


def _specimen_codex_markup(report: dict) -> str:
    codex = build_specimen_codex(report)
    cards = ""
    for specimen in codex["specimens"]:
        tells = ", ".join(str(item) for item in specimen.get("tells", []))
        cards += (
            '<article class="specimen-card">'
            f'<div class="specimen-rune">{escape(str(specimen.get("name", "?"))[:1])}</div>'
            f'<div class="specimen-topline">{escape(str(specimen.get("attack_family", "unknown")).replace("_", " "))}</div>'
            f'<h3>{escape(str(specimen.get("name", "Unknown Specimen")))}</h3>'
            f'<p>{escape(str(specimen.get("temperament", "")))}</p>'
            f'<div class="specimen-meta"><span>{int(specimen.get("sightings", 0))} sightings</span><span>{int(specimen.get("proven_sightings", 0))} proven bites</span><span>top score {int(specimen.get("highest_score", 0))}</span></div>'
            f'<p><strong>Tells:</strong> {escape(tells)}</p>'
            f'<p><strong>Containment:</strong> {escape(str(specimen.get("containment", "")))}</p>'
            "</article>"
        )
    return (
        '<section class="codex-panel">'
        '<div class="codex-header">'
        '<div class="eyebrow">Specimen Codex</div>'
        '<h2>Every boring finding gets a monster name.</h2>'
        '<p>Security artifacts are easier to remember when the failure mode has a shape. This codex turns the report into a field guide for what tried to bite the workflow.</p>'
        '</div>'
        f'<div class="specimen-grid">{cards}</div>'
        "</section>"
    )


def build_share_html(report: dict, *, source_label: str, title: str | None = None) -> str:
    """Render a single-file HTML artifact that is easy to publish or screenshot."""
    verdict, verdict_copy = _verdict(report)
    heading = title or "Honeypot Med Threat Snapshot"
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    engine = report.get("engine", {})
    launch_kit = build_launch_kit(report, title=heading, source_label=source_label)
    events_markup = "".join(_event_markup(event) for event in report.get("events", []))
    challenge_markup = _challenge_markup(report.get("challenge"))
    specimen_codex_markup = _specimen_codex_markup(report)
    launch_markup = "".join(
        [
            _copy_card("Headline", launch_kit["headline"]),
            _copy_card("X Post", launch_kit["x_post"]),
            _copy_card("LinkedIn Post", launch_kit["linkedin_post"]),
            _copy_card("Hacker News Title", launch_kit["hacker_news_title"]),
            _copy_card("Product Hunt Tagline", launch_kit["product_hunt_tagline"]),
            _copy_card("Product Hunt Description", launch_kit["product_hunt_description"]),
            _copy_card("GitHub Release Blurb", launch_kit["github_release_blurb"]),
            _copy_card("Email Subject", launch_kit["email_subject"]),
            _copy_card("Releases Page", launch_kit["releases_url"]),
            _copy_card("Install on macOS/Linux", launch_kit["install_macos_linux"]),
            _copy_card("Install on Windows", launch_kit["install_windows"]),
        ]
    )
    keywords = ", ".join(launch_kit["keywords"])
    structured_data = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": heading,
        "description": launch_kit["meta_description"],
        "keywords": launch_kit["keywords"],
        "about": [
            "prompt injection",
            "healthcare AI security",
            "open source security tooling",
        ],
        "publisher": {
            "@type": "Organization",
            "name": "ByteWorthy LLC",
            "url": launch_kit["repo_url"],
        },
    }
    hero = load_default_hero_data_uri()
    verdict_background = (
        "background:"
        " linear-gradient(180deg, rgba(17,24,28,0.18), rgba(17,24,28,0.62)),"
        f" url('{hero}') center/cover;"
        if hero
        else "background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(255,248,242,0.92)), linear-gradient(135deg, rgba(206, 64, 39, 0.12), rgba(37, 115, 84, 0.08));"
    )
    verdict_text = "white" if hero else "var(--muted)"
    verdict_value = "white" if hero else ("var(--accent-deep)" if verdict != "PASS" else "var(--safe)")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='18' fill='%231f2630'/%3E%3Ctext x='32' y='40' text-anchor='middle' font-size='22' font-family='Arial' font-weight='700' fill='white'%3EHM%3C/text%3E%3C/svg%3E" />
  <title>{escape(heading)}</title>
  <meta name="description" content="{escape(launch_kit['meta_description'])}" />
  <meta name="keywords" content="{escape(keywords)}" />
  <meta property="og:title" content="{escape(heading)}" />
  <meta property="og:description" content="{escape(launch_kit['meta_description'])}" />
  <meta property="og:type" content="website" />
  <meta property="og:image" content="social-card.svg" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{escape(heading)}" />
  <meta name="twitter:description" content="{escape(launch_kit['meta_description'])}" />
  <meta name="twitter:image" content="social-card.svg" />
  <script type="application/ld+json">{json.dumps(structured_data)}</script>
  <style>
    :root {{
      --bg: #f6efe3;
      --panel: rgba(255, 250, 244, 0.86);
      --panel-strong: rgba(255, 255, 255, 0.95);
      --ink: #1f2630;
      --muted: #57606a;
      --accent: #ce4027;
      --accent-deep: #8f1f12;
      --safe: #257354;
      --line: rgba(31, 38, 48, 0.12);
      --shadow: 0 22px 60px rgba(88, 44, 16, 0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(206, 64, 39, 0.18), transparent 28rem),
        radial-gradient(circle at top right, rgba(37, 115, 84, 0.14), transparent 24rem),
        linear-gradient(180deg, #fbf6ee 0%, var(--bg) 100%);
      font-family: "Avenir Next", "Helvetica Neue", "Segoe UI", sans-serif;
    }}
    .shell {{
      width: min(1160px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 40px 0 56px;
    }}
    .masthead {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
      flex-wrap: wrap;
    }}
    .brand {{
      display: inline-flex;
      align-items: center;
      gap: 12px;
    }}
    .brand-mark {{
      width: 42px;
      height: 42px;
      border-radius: 14px;
      display: grid;
      place-items: center;
      background: linear-gradient(135deg, #1f2630, #33414f);
      color: white;
      font-weight: 800;
      letter-spacing: 0.04em;
    }}
    .brand-copy {{
      display: grid;
      gap: 2px;
    }}
    .brand-name {{
      font-size: 15px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      font-weight: 800;
    }}
    .brand-tagline {{
      color: var(--muted);
      font-size: 13px;
    }}
    .masthead-links {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }}
    .masthead-links a,
    .artifact-links a {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.78);
      color: var(--ink);
      text-decoration: none;
      font-weight: 700;
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1.25fr 0.75fr;
      gap: 18px;
      align-items: stretch;
      margin-bottom: 18px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 28px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(12px);
    }}
    .hero-copy {{
      padding: 32px;
    }}
    .eyebrow {{
      display: inline-flex;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(31, 38, 48, 0.06);
      color: var(--muted);
      font-size: 12px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 16px 0 12px;
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif;
      font-size: clamp(2.3rem, 4vw, 4.4rem);
      line-height: 0.95;
      letter-spacing: -0.04em;
    }}
    .hero-copy p {{
      margin: 0;
      max-width: 60ch;
      font-size: 18px;
      line-height: 1.6;
      color: var(--muted);
    }}
    .verdict {{
      padding: 28px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      {verdict_background}
    }}
    .verdict-label {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.18em;
      color: {verdict_text};
    }}
    .verdict-value {{
      margin-top: 14px;
      font-size: clamp(2.2rem, 5vw, 5rem);
      line-height: 0.9;
      font-weight: 800;
      color: {verdict_value};
    }}
    .verdict-copy {{
      margin-top: 14px;
      color: {verdict_text};
      font-size: 16px;
      line-height: 1.6;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }}
    .metric {{
      padding: 20px 22px;
      background: var(--panel-strong);
      border: 1px solid var(--line);
      border-radius: 22px;
      box-shadow: var(--shadow);
    }}
    .metric-value {{
      font-size: 32px;
      font-weight: 800;
      line-height: 1;
      margin-bottom: 8px;
    }}
    .metric-label {{
      color: var(--muted);
      font-size: 14px;
    }}
    .context {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }}
    .context .panel {{
      padding: 22px;
      border-radius: 24px;
    }}
    .context h2 {{
      margin: 0 0 8px;
      font-size: 16px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .context p {{
      margin: 0;
      color: var(--muted);
      line-height: 1.6;
      font-size: 15px;
    }}
    .challenge-panel {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(180px, 0.32fr);
      gap: 18px;
      padding: 24px;
      margin-bottom: 18px;
    }}
    .challenge-copy h2 {{
      margin: 12px 0;
      font-size: clamp(1.8rem, 3vw, 3rem);
      line-height: 0.96;
      letter-spacing: -0.04em;
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif;
    }}
    .challenge-copy p {{
      margin: 0;
      color: var(--muted);
      line-height: 1.7;
      font-size: 16px;
    }}
    .challenge-score {{
      border-radius: 24px;
      background: linear-gradient(135deg, rgba(37,115,84,0.16), rgba(206,64,39,0.12));
      border: 1px solid var(--line);
      padding: 22px;
      display: grid;
      place-items: center;
      text-align: center;
    }}
    .challenge-score strong {{
      display: block;
      font-size: 38px;
      line-height: 1;
    }}
    .challenge-score span {{
      color: var(--muted);
      margin-top: 8px;
    }}
    .baseline-grid {{
      grid-column: 1 / -1;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 12px;
    }}
    .baseline-card {{
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: rgba(255,255,255,0.72);
    }}
    .baseline-card strong {{
      display: block;
      margin: 8px 0 4px;
      font-size: 20px;
    }}
    .baseline-card span,
    .baseline-card p {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }}
    .baseline-card p {{
      margin: 8px 0 0;
    }}
    .baseline-topline {{
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }}
    .events {{
      display: grid;
      gap: 16px;
      margin-bottom: 18px;
    }}
    .codex-panel {{
      margin-bottom: 18px;
      display: grid;
      gap: 16px;
    }}
    .codex-header {{
      padding: 26px;
      border-radius: 28px;
      border: 1px solid rgba(255,255,255,0.14);
      color: #fffaf4;
      background:
        radial-gradient(circle at 20% 20%, rgba(206, 64, 39, 0.45), transparent 18rem),
        radial-gradient(circle at 90% 10%, rgba(37, 115, 84, 0.32), transparent 18rem),
        linear-gradient(135deg, #151a21 0%, #2a1612 100%);
      box-shadow: var(--shadow);
    }}
    .codex-header .eyebrow {{
      color: rgba(255,250,244,0.72);
      background: rgba(255,255,255,0.09);
    }}
    .codex-header h2 {{
      margin: 14px 0 10px;
      max-width: 760px;
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif;
      font-size: clamp(2rem, 4vw, 4.2rem);
      line-height: 0.92;
      letter-spacing: -0.05em;
    }}
    .codex-header p {{
      margin: 0;
      max-width: 760px;
      color: rgba(255,250,244,0.72);
      line-height: 1.7;
      font-size: 17px;
    }}
    .specimen-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 14px;
    }}
    .specimen-card {{
      position: relative;
      overflow: hidden;
      padding: 22px;
      min-height: 300px;
      border-radius: 26px;
      border: 1px solid rgba(31, 38, 48, 0.18);
      background:
        linear-gradient(180deg, rgba(255,250,244,0.98), rgba(243,230,210,0.92));
      box-shadow: var(--shadow);
    }}
    .specimen-card:nth-child(2n) {{
      transform: translateY(8px) rotate(-0.7deg);
    }}
    .specimen-card:nth-child(3n) {{
      transform: translateY(-4px) rotate(0.6deg);
    }}
    .specimen-rune {{
      position: absolute;
      right: -14px;
      top: -26px;
      font-size: 150px;
      font-weight: 900;
      line-height: 1;
      color: rgba(206,64,39,0.09);
    }}
    .specimen-topline {{
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.16em;
    }}
    .specimen-card h3 {{
      margin: 12px 0 10px;
      font-size: 26px;
      line-height: 1;
    }}
    .specimen-card p {{
      position: relative;
      margin: 0 0 12px;
      color: var(--muted);
      line-height: 1.6;
    }}
    .specimen-card strong {{
      color: var(--ink);
    }}
    .specimen-meta {{
      position: relative;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 12px 0;
    }}
    .specimen-meta span {{
      padding: 7px 9px;
      border-radius: 999px;
      background: rgba(31,38,48,0.07);
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }}
    .event-card {{
      padding: 24px;
      background: var(--panel-strong);
      border: 1px solid var(--line);
      border-radius: 26px;
      box-shadow: var(--shadow);
    }}
    .event-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 14px;
    }}
    .severity-pill {{
      display: inline-flex;
      padding: 9px 12px;
      border-radius: 999px;
      font-size: 12px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      font-weight: 700;
      background: rgba(31, 38, 48, 0.08);
    }}
    .severity-critical, .severity-high {{
      color: white;
      background: linear-gradient(135deg, #b02719, #e25a37);
    }}
    .severity-medium {{
      color: #7a4d00;
      background: linear-gradient(135deg, #f4ca6b, #f8df9a);
    }}
    .severity-low {{
      color: #1d6549;
      background: linear-gradient(135deg, #bee3d2, #d7f1e5);
    }}
    .event-score {{
      font-size: 44px;
      font-weight: 800;
      line-height: 1;
    }}
    .event-card h3 {{
      margin: 0 0 12px;
      font-size: 24px;
      line-height: 1.2;
    }}
    .event-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 18px;
      color: var(--muted);
      font-size: 14px;
    }}
    .finding-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 12px;
    }}
    .finding {{
      min-height: 100%;
      padding: 16px;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(255,255,255,0.86), rgba(248,243,236,0.92));
    }}
    .finding-topline {{
      margin-bottom: 8px;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--muted);
    }}
    .finding h4 {{
      margin: 0 0 8px;
      font-size: 18px;
      line-height: 1.25;
    }}
    .finding-meta {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 12px;
    }}
    .evidence-list {{
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
      line-height: 1.6;
      font-size: 14px;
    }}
    .empty-state {{
      padding: 18px;
      border-radius: 18px;
      border: 1px dashed var(--line);
      color: var(--muted);
      background: rgba(255,255,255,0.72);
    }}
    .footer {{
      margin-top: 18px;
      padding: 20px 24px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.6;
      text-align: center;
    }}
    .launch-kit {{
      display: grid;
      gap: 16px;
      margin-bottom: 18px;
    }}
    .launch-headline {{
      padding: 24px;
    }}
    .launch-headline h2,
    .launch-copy-grid h2 {{
      margin: 0 0 8px;
      font-size: 16px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .launch-headline p {{
      margin: 0;
      color: var(--muted);
      line-height: 1.7;
      font-size: 16px;
    }}
    .launch-copy-grid {{
      display: grid;
      gap: 14px;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }}
    .copy-card {{
      padding: 20px;
      background: var(--panel-strong);
      border: 1px solid var(--line);
      border-radius: 22px;
      box-shadow: var(--shadow);
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    .copy-card h3 {{
      margin: 0;
      font-size: 15px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .copy-card p {{
      margin: 0;
      color: var(--muted);
      line-height: 1.65;
      white-space: pre-wrap;
      font-size: 14px;
    }}
    .copy-button {{
      width: fit-content;
      border: 0;
      border-radius: 999px;
      padding: 10px 14px;
      background: var(--accent);
      color: white;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }}
    .copy-button:hover {{
      background: var(--accent-deep);
    }}
    .launch-links {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 14px;
    }}
    .artifact-links {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .artifact-links a {{
      min-height: 56px;
    }}
    @media (max-width: 940px) {{
      .hero,
      .context,
      .challenge-panel,
      .metrics,
      .artifact-links {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <div class="masthead">
      <div class="brand">
        <div class="brand-mark">HM</div>
        <div class="brand-copy">
          <div class="brand-name">Honeypot Med</div>
          <div class="brand-tagline">Prompt-injection evidence for healthcare AI</div>
        </div>
      </div>
      <div class="masthead-links">
        <a href="{escape(launch_kit['public_site_url'])}" target="_blank" rel="noreferrer">Public site</a>
        <a href="{escape(launch_kit['releases_url'])}" target="_blank" rel="noreferrer">Releases</a>
        <a href="{escape(launch_kit['repo_url'])}" target="_blank" rel="noreferrer">GitHub repo</a>
      </div>
    </div>
    <section class="hero">
      <article class="panel hero-copy">
        <div class="eyebrow">Prompt Injection Evidence</div>
        <h1>{escape(heading)}</h1>
        <p>{escape(verdict_copy)}</p>
      </article>
      <aside class="panel verdict">
        <div>
          <div class="verdict-label">Launch Verdict</div>
          <div class="verdict-value">{escape(verdict)}</div>
        </div>
        <div class="verdict-copy">Generated by Honeypot Med as a standalone share page for founders, security teams, and buyers.</div>
      </aside>
    </section>

    <section class="metrics">
      {_metric("Prompts Analyzed", str(int(report.get("total_prompts", 0))))}
      {_metric("Highest Risk", str(max((int(event.get("risk_score", 0)) for event in report.get("events", [])), default=0)))}
      {_metric("High-Risk Events", str(int(report.get("high_risk_count", 0))))}
      {_metric("Proven Findings", str(int(report.get("proven_findings_count", 0))))}
      {_metric("Unproven Hypotheses", str(int(report.get("unproven_count", 0))))}
    </section>

    <section class="artifact-links">
      <a href="proof-dossier.html" target="_blank" rel="noreferrer">Open visual proof dossier</a>
      <a href="offline-proof.pdf" target="_blank" rel="noreferrer">Open offline proof PDF</a>
      <a href="ui-mockup.html" target="_blank" rel="noreferrer">Open UI mockup</a>
      <a href="report.json" target="_blank" rel="noreferrer">Open JSON report</a>
      <a href="report.md" target="_blank" rel="noreferrer">Open Markdown summary</a>
      <a href="summary.pdf" target="_blank" rel="noreferrer">Open PDF brief</a>
      <a href="social-card.svg" target="_blank" rel="noreferrer">Open social card</a>
      <a href="badge.svg" target="_blank" rel="noreferrer">Open README badge</a>
      <a href="honeypot-med.sarif" target="_blank" rel="noreferrer">Open SARIF export</a>
      <a href="otel-logs.json" target="_blank" rel="noreferrer">Open OTEL logs</a>
      <a href="inquiry-notebook.md" target="_blank" rel="noreferrer">Open inquiry notebook</a>
      <a href="experiment-plan.md" target="_blank" rel="noreferrer">Open experiment plan</a>
      <a href="eval-kit.md" target="_blank" rel="noreferrer">Open eval kit</a>
    </section>

    <section class="context">
      <article class="panel">
        <h2>Source</h2>
        <p>{escape(source_label)}</p>
      </article>
      <article class="panel">
        <h2>Engine</h2>
        <p>{escape(str(engine.get("provider", "deterministic-local")))} in {escape(str(engine.get("selected_mode", engine.get("requested_mode", "local"))))} mode.</p>
      </article>
      <article class="panel">
        <h2>Generated</h2>
        <p>{escape(generated_at)}</p>
      </article>
    </section>

    {challenge_markup}
    {specimen_codex_markup}

    <section class="launch-kit">
      <article class="panel launch-headline">
        <h2>Launch-Ready Copy</h2>
        <p>{escape(launch_kit['summary'])}</p>
        <p>{escape(launch_kit['evidence_line'])}</p>
        <div class="launch-links">
          <a href="{escape(launch_kit['public_site_url'])}" target="_blank" rel="noreferrer">Public Site</a>
          <a href="{escape(launch_kit['releases_url'])}" target="_blank" rel="noreferrer">Releases</a>
          <a href="{escape(launch_kit['repo_url'])}" target="_blank" rel="noreferrer">GitHub Repo</a>
          <a href="launch-kit.md" target="_blank" rel="noreferrer">Launch Kit Markdown</a>
          <a href="launch-kit.json" target="_blank" rel="noreferrer">Launch Kit JSON</a>
        </div>
      </article>
      <div class="launch-copy-grid">
        {launch_markup}
      </div>
    </section>

    <section class="events">
      {events_markup}
    </section>

    <footer class="panel footer">
      This page was generated locally. It is safe to publish as a proof artifact, screenshot, or buyer-facing security snapshot.
    </footer>
  </main>
  <script>
    Array.from(document.querySelectorAll(".copy-button")).forEach((button) => {{
      button.addEventListener("click", async () => {{
        const value = button.dataset.copy || "";
        try {{
          await navigator.clipboard.writeText(value);
          const original = button.textContent;
          button.textContent = "Copied";
          setTimeout(() => {{
            button.textContent = original;
          }}, 1200);
        }} catch (_error) {{
          button.textContent = "Copy failed";
        }}
      }});
    }});
  </script>
</body>
</html>
"""
