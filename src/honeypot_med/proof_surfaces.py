"""Visual proof surfaces for local-first Honeypot Med artifacts."""

from __future__ import annotations

import textwrap
from datetime import datetime, timezone
from html import escape

from .specimens import build_specimen_codex


def _metric(report: dict, key: str) -> int:
    return int(report.get(key, 0) or 0)


def _top_event(report: dict) -> dict:
    events = list(report.get("events", []))
    return max(events, key=lambda event: int(event.get("risk_score", 0)), default={})


def _prompt_excerpt(text: str, limit: int = 160) -> str:
    value = " ".join(str(text).split())
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def _artifact_links() -> str:
    artifacts = [
        ("Visual dossier", "proof-dossier.html", "Designed HTML proof surface"),
        ("PDF proof", "offline-proof.pdf", "Attachment-ready document"),
        ("UI mockup", "ui-mockup.html", "Static product surface mockup"),
        ("Plain proof", "offline-proof.txt", "Machine-readable free-path note"),
        ("Field guide", "field-guide.md", "Specimen notebook"),
        ("Trap ledger", "trap-ledger.csv", "Row-level evidence"),
    ]
    return "\n".join(
        (
            '<a class="artifact" href="{href}">'
            "<strong>{label}</strong><span>{note}</span><small>{href}</small></a>"
        ).format(href=escape(href), label=escape(label), note=escape(note))
        for label, href, note in artifacts
    )


def _specimen_cards(report: dict) -> str:
    codex = build_specimen_codex(report)
    specimens = list(codex.get("specimens", []))[:6]
    if not specimens:
        return '<article class="specimen"><strong>No specimens sighted</strong><span>The run did not trigger a named failure archetype.</span></article>'
    return "\n".join(
        (
            '<article class="specimen">'
            '<div class="specimen-top"><strong>{name}</strong><span>{sightings} sightings</span></div>'
            "<p>{temperament}</p>"
            "<small>{containment}</small>"
            "</article>"
        ).format(
            name=escape(str(specimen.get("name", "Unknown Specimen"))),
            sightings=escape(str(specimen.get("sightings", 0))),
            temperament=escape(str(specimen.get("temperament", "Unclassified behavior"))),
            containment=escape(str(specimen.get("containment", "Review the evidence."))),
        )
        for specimen in specimens
    )


def _trap_rows(ledger: list[dict], *, limit: int = 8) -> str:
    if not ledger:
        return '<article class="trap-row"><strong>No traps observed</strong><span>Run a prompt or pack to populate this surface.</span></article>'
    return "\n".join(
        (
            '<article class="trap-row">'
            '<div><strong>Trap {trap}</strong><span>{severity} / risk {risk}</span></div>'
            '<p>{prompt}</p>'
            '<small>{specimens}</small>'
            "</article>"
        ).format(
            trap=escape(str(row.get("trap", ""))),
            severity=escape(str(row.get("severity", "low")).upper()),
            risk=escape(str(row.get("risk_score", 0))),
            prompt=escape(str(row.get("prompt_excerpt", ""))),
            specimens=escape(str(row.get("specimens", "No named specimen")) or "No named specimen"),
        )
        for row in ledger[:limit]
    )


def build_proof_dossier_html(
    report: dict,
    ledger: list[dict],
    *,
    source_label: str,
    title: str,
) -> str:
    """Return an aesthetic, print-friendly offline proof dossier."""
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = len(ledger)
    survived = sum(1 for row in ledger if row.get("survived") == "yes")
    bitten = max(total - survived, 0)
    top = _top_event(report)
    top_prompt = _prompt_excerpt(str(top.get("prompt", "No prompt captured.")))
    top_severity = str(top.get("severity", "review")).upper()
    top_score = int(top.get("risk_score", 0) or 0)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(title)} Proof Dossier</title>
  <style>
    :root {{
      --paper: #f7efe2;
      --panel: rgba(255, 252, 245, 0.92);
      --ink: #172027;
      --muted: #65706e;
      --line: rgba(23, 32, 39, 0.13);
      --red: #bc432f;
      --teal: #1f705f;
      --ochre: #d5963d;
      --shadow: 0 28px 90px rgba(75, 45, 23, 0.15);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 8% 8%, rgba(188, 67, 47, 0.20), transparent 28rem),
        radial-gradient(circle at 96% 4%, rgba(31, 112, 95, 0.18), transparent 26rem),
        linear-gradient(180deg, #fff9ef 0%, var(--paper) 100%);
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .page {{
      width: min(1180px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 32px 0 52px;
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 20px;
      align-items: stretch;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 32px;
      box-shadow: var(--shadow);
    }}
    .intro {{
      padding: clamp(28px, 5vw, 56px);
      position: relative;
      overflow: hidden;
    }}
    .intro::after {{
      content: "";
      position: absolute;
      width: 260px;
      height: 260px;
      right: -90px;
      top: -80px;
      border: 34px solid rgba(188, 67, 47, 0.12);
      border-radius: 50%;
    }}
    .eyebrow {{
      display: inline-flex;
      padding: 9px 13px;
      border-radius: 999px;
      background: rgba(23, 32, 39, 0.07);
      color: var(--muted);
      letter-spacing: 0.14em;
      text-transform: uppercase;
      font-size: 12px;
      font-weight: 800;
    }}
    h1 {{
      max-width: 11ch;
      margin: 18px 0 16px;
      font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif;
      font-size: clamp(3.2rem, 8vw, 7.4rem);
      line-height: 0.86;
      letter-spacing: -0.065em;
    }}
    .lede {{
      max-width: 58ch;
      color: var(--muted);
      font-size: 19px;
      line-height: 1.7;
    }}
    .stamp {{
      display: grid;
      gap: 14px;
      padding: 28px;
      background:
        linear-gradient(150deg, rgba(23, 32, 39, 0.95), rgba(29, 56, 54, 0.94)),
        radial-gradient(circle at top right, rgba(213, 150, 61, 0.28), transparent 18rem);
      color: #fff8ec;
      border-color: rgba(255, 255, 255, 0.12);
    }}
    .stamp h2 {{
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif;
      font-size: 38px;
      line-height: 1;
      letter-spacing: -0.04em;
    }}
    .seal {{
      aspect-ratio: 1;
      border-radius: 32px;
      display: grid;
      place-items: center;
      border: 1px solid rgba(255, 255, 255, 0.18);
      background:
        radial-gradient(circle, rgba(213, 150, 61, 0.42), transparent 54%),
        repeating-linear-gradient(135deg, rgba(255,255,255,0.10), rgba(255,255,255,0.10) 1px, transparent 1px, transparent 12px);
      font-size: clamp(4rem, 9vw, 8rem);
      font-weight: 900;
      letter-spacing: -0.1em;
    }}
    .stamp p, .stamp small {{ color: rgba(255, 248, 236, 0.76); line-height: 1.6; margin: 0; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin: 20px 0;
    }}
    .metric {{
      padding: 20px;
      border-radius: 24px;
      background: rgba(255, 252, 245, 0.88);
      border: 1px solid var(--line);
    }}
    .metric strong {{ display: block; font-size: 38px; line-height: 1; letter-spacing: -0.04em; }}
    .metric span {{ display: block; margin-top: 8px; color: var(--muted); font-size: 13px; text-transform: uppercase; letter-spacing: 0.11em; }}
    .section {{
      margin-top: 20px;
      padding: 28px;
    }}
    .section h2 {{
      margin: 0 0 14px;
      font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif;
      font-size: 34px;
      letter-spacing: -0.035em;
    }}
    .proof-grid, .specimen-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }}
    .artifact, .specimen, .trap-row {{
      display: block;
      color: inherit;
      text-decoration: none;
      padding: 18px;
      border-radius: 22px;
      background: rgba(255, 255, 255, 0.72);
      border: 1px solid var(--line);
    }}
    .artifact strong, .specimen strong, .trap-row strong {{ display: block; font-size: 17px; }}
    .artifact span, .specimen p, .trap-row p {{ color: var(--muted); line-height: 1.55; }}
    .artifact small, .specimen small, .trap-row small {{ color: var(--teal); font-weight: 800; }}
    .specimen-top, .trap-row div {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 12px;
    }}
    .specimen-top span, .trap-row div span {{
      color: var(--red);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.11em;
      font-weight: 800;
    }}
    .trap-list {{ display: grid; gap: 10px; }}
    .top-prompt {{
      padding: 22px;
      border-radius: 24px;
      background: linear-gradient(135deg, rgba(188,67,47,0.10), rgba(31,112,95,0.08));
      border: 1px solid var(--line);
      color: var(--muted);
      line-height: 1.65;
    }}
    .cta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }}
    .cta a {{
      color: #fff8ec;
      text-decoration: none;
      background: var(--ink);
      border-radius: 999px;
      padding: 13px 16px;
      font-weight: 800;
    }}
    .cta a.secondary {{ color: var(--ink); background: rgba(23, 32, 39, 0.08); }}
    @media (max-width: 900px) {{
      .hero, .metrics, .proof-grid, .specimen-grid {{ grid-template-columns: 1fr; }}
      h1 {{ max-width: 100%; }}
    }}
    @media print {{
      body {{ background: white; }}
      .page {{ width: 100%; padding: 0; }}
      .card {{ box-shadow: none; break-inside: avoid; }}
      .cta {{ display: none; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <article class="card intro">
        <span class="eyebrow">Offline proof dossier</span>
        <h1>{escape(title)}</h1>
        <p class="lede">A visual, shareable proof packet generated by local deterministic code. The free path needs no model API call, no hosted enrichment, and no paid dependency.</p>
        <div class="cta">
          <a href="offline-proof.pdf">Open PDF proof</a>
          <a class="secondary" href="ui-mockup.html">Open UI mockup</a>
          <a class="secondary" href="offline-proof.txt">Open text proof</a>
        </div>
      </article>
      <aside class="card stamp">
        <div class="seal">HM</div>
        <h2>Free path verified</h2>
        <p>Source: {escape(source_label)}<br />Generated: {escape(generated)}</p>
        <small>Default artifacts are produced from local files and standard-library rendering.</small>
      </aside>
    </section>
    <section class="metrics">
      <article class="metric"><strong>{total}</strong><span>Traps observed</span></article>
      <article class="metric"><strong>{survived}</strong><span>Survived</span></article>
      <article class="metric"><strong>{bitten}</strong><span>Proven bites</span></article>
      <article class="metric"><strong>{top_score}</strong><span>Top risk</span></article>
    </section>
    <section class="card section">
      <h2>Top signal</h2>
      <div class="top-prompt"><strong>{escape(top_severity)} / risk {top_score}</strong><br />{escape(top_prompt)}</div>
    </section>
    <section class="card section">
      <h2>Open the packet</h2>
      <div class="proof-grid">{_artifact_links()}</div>
    </section>
    <section class="card section">
      <h2>Specimen shelf</h2>
      <div class="specimen-grid">{_specimen_cards(report)}</div>
    </section>
    <section class="card section">
      <h2>Trap ledger preview</h2>
      <div class="trap-list">{_trap_rows(ledger)}</div>
    </section>
  </main>
</body>
</html>
"""


def build_ui_mockup_html(
    report: dict,
    ledger: list[dict],
    *,
    source_label: str,
    title: str,
) -> str:
    """Return a static UI mockup that stakeholders can open without a server."""
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    top = _top_event(report)
    severity = str(top.get("severity", "review")).upper()
    top_score = int(top.get("risk_score", 0) or 0)
    top_prompt = _prompt_excerpt(str(top.get("prompt", "Choose a prompt or pack to inspect.")), 110)
    trap_rows = _trap_rows(ledger, limit=4)
    specimen_cards = _specimen_cards(report)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(title)} UI Mockup</title>
  <style>
    :root {{
      --ink: #141d22;
      --paper: #f5ead8;
      --card: #fffaf1;
      --line: rgba(20, 29, 34, 0.12);
      --red: #bf432e;
      --green: #1d725f;
      --gold: #dda348;
      --muted: #67716f;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      background:
        linear-gradient(115deg, rgba(191,67,46,0.16), transparent 34%),
        radial-gradient(circle at 88% 12%, rgba(29,114,95,0.20), transparent 28rem),
        var(--paper);
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .stage {{
      width: min(1240px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 34px 0 48px;
    }}
    .topbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
    }}
    .brand {{ display: flex; align-items: center; gap: 12px; font-weight: 900; letter-spacing: -0.02em; }}
    .mark {{
      width: 46px;
      height: 46px;
      border-radius: 16px;
      display: grid;
      place-items: center;
      background: var(--ink);
      color: #fff6e9;
    }}
    .pill {{
      border: 1px solid var(--line);
      background: rgba(255, 250, 241, 0.72);
      border-radius: 999px;
      padding: 10px 13px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 800;
    }}
    .app {{
      display: grid;
      grid-template-columns: 250px 1fr;
      gap: 18px;
      padding: 18px;
      border-radius: 38px;
      background: rgba(255, 250, 241, 0.72);
      border: 1px solid rgba(255,255,255,0.72);
      box-shadow: 0 34px 110px rgba(71, 45, 22, 0.18);
      backdrop-filter: blur(18px);
    }}
    .sidebar, .workspace, .panel {{
      border: 1px solid var(--line);
      background: rgba(255, 250, 241, 0.86);
      border-radius: 28px;
    }}
    .sidebar {{ padding: 20px; display: grid; align-content: start; gap: 10px; }}
    .nav-item {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 13px 14px;
      border-radius: 18px;
      color: var(--muted);
    }}
    .nav-item.active {{ background: var(--ink); color: #fff6e9; }}
    .workspace {{ padding: 22px; }}
    .hero {{
      display: grid;
      grid-template-columns: 1fr 0.85fr;
      gap: 16px;
      margin-bottom: 16px;
    }}
    h1 {{
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif;
      font-size: clamp(3.4rem, 7vw, 6.5rem);
      line-height: 0.85;
      letter-spacing: -0.065em;
    }}
    .hero-copy {{
      min-height: 340px;
      padding: 30px;
      border-radius: 28px;
      background:
        radial-gradient(circle at top right, rgba(221,163,72,0.28), transparent 16rem),
        linear-gradient(145deg, rgba(20,29,34,0.96), rgba(29,64,57,0.94));
      color: #fff6e9;
      position: relative;
      overflow: hidden;
    }}
    .hero-copy p {{ max-width: 44rem; color: rgba(255,246,233,0.72); line-height: 1.65; font-size: 18px; }}
    .hero-copy::after {{
      content: "";
      position: absolute;
      right: -80px;
      bottom: -100px;
      width: 280px;
      height: 280px;
      border: 36px solid rgba(255, 246, 233, 0.12);
      border-radius: 50%;
    }}
    .verdict-card {{
      padding: 26px;
      display: grid;
      gap: 18px;
    }}
    .verdict {{
      display: grid;
      place-items: center;
      min-height: 176px;
      border-radius: 28px;
      background: linear-gradient(135deg, rgba(191,67,46,0.15), rgba(29,114,95,0.12));
      border: 1px dashed rgba(20, 29, 34, 0.18);
      text-align: center;
    }}
    .verdict strong {{ font-size: 68px; line-height: 0.9; letter-spacing: -0.08em; }}
    .verdict span {{ color: var(--muted); font-weight: 900; text-transform: uppercase; letter-spacing: 0.12em; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }}
    .metric, .output {{
      padding: 18px;
      border-radius: 22px;
      background: var(--card);
      border: 1px solid var(--line);
    }}
    .metric strong {{ display: block; font-size: 34px; line-height: 1; }}
    .metric span, .output span {{ display: block; color: var(--muted); margin-top: 7px; }}
    .lower {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }}
    .panel {{ padding: 20px; }}
    .panel h2 {{ margin: 0 0 12px; font-size: 20px; }}
    .trap-list, .specimen-grid {{ display: grid; gap: 10px; }}
    .specimen-grid {{ grid-template-columns: 1fr 1fr; }}
    .specimen, .trap-row {{
      padding: 14px;
      border-radius: 18px;
      background: rgba(255,255,255,0.62);
      border: 1px solid var(--line);
    }}
    .specimen p, .trap-row p {{ color: var(--muted); line-height: 1.5; }}
    .specimen small, .trap-row small {{ color: var(--green); font-weight: 900; }}
    .specimen-top, .trap-row div {{ display: flex; justify-content: space-between; gap: 12px; }}
    .specimen-top span, .trap-row div span {{ color: var(--red); font-size: 11px; font-weight: 900; letter-spacing: 0.1em; }}
    .outputs {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-top: 16px;
    }}
    .output strong {{ display: block; }}
    @media (max-width: 980px) {{
      .app, .hero, .lower, .metrics, .outputs, .specimen-grid {{ grid-template-columns: 1fr; }}
      .sidebar {{ display: none; }}
    }}
  </style>
</head>
<body>
  <main class="stage">
    <header class="topbar">
      <div class="brand"><div class="mark">HM</div><div>Honeypot Med Studio Mockup</div></div>
      <div class="pill">Generated locally / {escape(generated)}</div>
    </header>
    <section class="app">
      <aside class="sidebar">
        <div class="nav-item active"><span>Proof console</span><strong>01</strong></div>
        <div class="nav-item"><span>Trap ledger</span><strong>{len(ledger)}</strong></div>
        <div class="nav-item"><span>Specimens</span><strong>{len(build_specimen_codex(report).get("specimens", []))}</strong></div>
        <div class="nav-item"><span>Exports</span><strong>6</strong></div>
        <div class="nav-item"><span>Network</span><strong>Off</strong></div>
      </aside>
      <section class="workspace">
        <div class="hero">
          <article class="hero-copy">
            <div class="pill">Visual packet mockup</div>
            <h1>{escape(title)}</h1>
            <p>{escape(top_prompt)}</p>
          </article>
          <article class="panel verdict-card">
            <div class="verdict"><div><span>{escape(severity)}</span><strong>{top_score}</strong></div></div>
            <p class="pill">Source: {escape(source_label)}</p>
          </article>
        </div>
        <div class="metrics">
          <article class="metric"><strong>{_metric(report, "total_prompts")}</strong><span>Prompts analyzed</span></article>
          <article class="metric"><strong>{_metric(report, "high_risk_count")}</strong><span>High risk</span></article>
          <article class="metric"><strong>{_metric(report, "proven_findings_count")}</strong><span>Proven findings</span></article>
        </div>
        <section class="lower">
          <article class="panel"><h2>Trap ledger preview</h2><div class="trap-list">{trap_rows}</div></article>
          <article class="panel"><h2>Specimen shelf</h2><div class="specimen-grid">{specimen_cards}</div></article>
        </section>
        <section class="outputs">
          <article class="output"><strong>proof-dossier.html</strong><span>Visual proof surface</span></article>
          <article class="output"><strong>offline-proof.pdf</strong><span>Attachment-ready proof</span></article>
          <article class="output"><strong>summary.pdf</strong><span>Executive brief</span></article>
        </section>
      </section>
    </section>
  </main>
</body>
</html>
"""


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_offline_proof_pdf(
    report: dict,
    ledger: list[dict],
    *,
    source_label: str,
    title: str,
) -> bytes:
    """Return a small no-dependency PDF proof document."""
    width = 612
    height = 792
    page_contents: list[str] = []
    content: list[str] = []
    y = 736

    def push_page() -> None:
        nonlocal content, y
        if content:
            page_contents.append("\n".join(content))
        content = []
        y = 736
        content.append("0.969 0.933 0.855 rg 0 0 612 792 re f")
        content.append("0.078 0.114 0.133 rg 36 704 540 52 re f")
        content.append("0.741 0.263 0.181 rg 36 704 132 52 re f")

    def ensure_space(step: int) -> None:
        if y - step < 54:
            push_page()

    def add_text(text: str, *, size: int = 11, x: int = 48, bold: bool = False, color: str = "0.078 0.114 0.133") -> None:
        nonlocal y
        ensure_space(size + 12)
        font = "F2" if bold else "F1"
        safe = _pdf_escape(text.encode("latin-1", errors="replace").decode("latin-1"))
        content.append(f"{color} rg BT /{font} {size} Tf {x} {y} Td ({safe}) Tj ET")
        y -= size + 8

    def add_wrapped(text: str, *, size: int = 11, x: int = 48, width_chars: int = 78, bold: bool = False) -> None:
        for line in textwrap.wrap(text, width=width_chars) or [""]:
            add_text(line, size=size, x=x, bold=bold)

    push_page()
    content.append("1 0.965 0.910 rg BT /F2 12 Tf 52 722 Td (HONEYPOT MED) Tj ET")
    content.append("1 0.965 0.910 rg BT /F2 20 Tf 182 722 Td (Offline Proof Dossier) Tj ET")
    y = 672
    add_wrapped(title, size=24, bold=True, width_chars=36)
    add_text("Generated by local deterministic code. No model API call, paid hosted service, or remote enrichment is required for the free path.", size=11)
    add_text(f"Source: {source_label}", size=10)
    add_text(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", size=10)
    add_text("", size=4)

    metrics = [
        f"Traps observed: {len(ledger)}",
        f"Traps survived: {sum(1 for row in ledger if row.get('survived') == 'yes')}",
        f"High-risk events: {_metric(report, 'high_risk_count')}",
        f"Proven findings: {_metric(report, 'proven_findings_count')}",
    ]
    add_text("Run summary", size=15, bold=True)
    for metric in metrics:
        add_text(metric, size=11, x=60)
    add_text("", size=4)

    top = _top_event(report)
    add_text("Top signal", size=15, bold=True)
    add_text(
        f"{str(top.get('severity', 'review')).upper()} / risk {int(top.get('risk_score', 0) or 0)}",
        size=12,
        x=60,
        bold=True,
    )
    add_wrapped(str(top.get("prompt", "No prompt captured.")), size=10, x=60, width_chars=76)
    add_text("", size=4)

    add_text("Included visual artifacts", size=15, bold=True)
    for name in ("proof-dossier.html", "ui-mockup.html", "offline-proof.txt", "field-guide.md", "trap-ledger.csv"):
        add_text(name, size=11, x=60)
    add_text("", size=4)

    add_text("Trap ledger preview", size=15, bold=True)
    for row in ledger[:10]:
        add_text(
            f"Trap {row.get('trap')}: {str(row.get('severity', 'low')).upper()} / risk {row.get('risk_score', 0)}",
            size=11,
            x=60,
            bold=True,
        )
        add_wrapped(str(row.get("prompt_excerpt", "")), size=9, x=72, width_chars=74)

    if content:
        page_contents.append("\n".join(content))

    object_map: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        4: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
    }
    page_ids: list[int] = []
    next_id = 5
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
            f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {content_id} 0 R >>"
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
        pdf.extend(f"{offsets.get(obj_id, 0):010d} 00000 n\n".encode("latin-1"))
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
