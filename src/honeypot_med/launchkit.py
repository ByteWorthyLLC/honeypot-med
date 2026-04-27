"""Distribution and launch-copy helpers for public-facing artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone


PUBLIC_SITE_URL = "https://byteworthyllc.github.io/honeypot-med/"
REPO_URL = "https://github.com/ByteWorthyLLC/honeypot-med"
RELEASES_URL = f"{PUBLIC_SITE_URL}releases/"
INSTALL_MACOS_LINUX = (
    "curl -fsSL "
    "https://raw.githubusercontent.com/ByteWorthyLLC/honeypot-med/main/scripts/bootstrap/install.sh | bash"
)
INSTALL_WINDOWS = (
    'powershell -ExecutionPolicy Bypass -Command '
    '"iwr https://raw.githubusercontent.com/ByteWorthyLLC/honeypot-med/main/scripts/bootstrap/install.ps1 '
    '-UseBasicParsing | iex"'
)


def bundle_verdict(report: dict) -> str:
    severity = report.get("severity_counts", {})
    if int(severity.get("critical", 0)) > 0 or int(severity.get("high", 0)) > 0:
        return "BLOCK"
    if int(severity.get("medium", 0)) > 0:
        return "REVIEW"
    return "PASS"


def build_launch_kit(report: dict, *, title: str, source_label: str) -> dict:
    events = list(report.get("events", []))
    top_event = max(events, key=lambda event: int(event.get("risk_score", 0)), default={})
    verdict = bundle_verdict(report)
    total_prompts = int(report.get("total_prompts", 0))
    high_risk = int(report.get("high_risk_count", 0))
    proven = int(report.get("proven_findings_count", 0))
    top_score = int(top_event.get("risk_score", 0))
    prompt_excerpt = str(top_event.get("prompt", "")).strip()
    if len(prompt_excerpt) > 140:
        prompt_excerpt = prompt_excerpt[:137] + "..."

    short_summary = (
        f"{title} analyzed {total_prompts} prompt"
        f"{'' if total_prompts == 1 else 's'} from {source_label} and returned a {verdict} verdict "
        f"with {proven} proven finding"
        f"{'' if proven == 1 else 's'} and a top score of {top_score}."
    )
    evidence_line = (
        f"Top finding score: {top_score}. High-risk events: {high_risk}. "
        f"Representative prompt: \"{prompt_excerpt or 'No prompt excerpt available.'}\""
    )
    headline = f"{title}: prompt-injection evidence for healthcare AI"
    meta_description = (
        f"{title} is a local-first prompt-injection proof page for healthcare AI. "
        f"Verdict: {verdict}. Top score: {top_score}. Proven findings: {proven}."
    )
    x_post = (
        f"{title} just produced a {verdict} verdict for a healthcare AI workflow. "
        f"{proven} proven findings, top score {top_score}, visual dossier, PDF proof, UI mockup, and social card. "
        f"Open source, local-first, no API keys. {PUBLIC_SITE_URL}"
    )
    linkedin_post = (
        f"We ran Honeypot Med against {source_label} and generated a {verdict} verdict.\n\n"
        f"{short_summary}\n"
        f"{evidence_line}\n\n"
        f"Honeypot Med is open source, local-first, and built so teams can paste a risky prompt, "
        f"inspect the evidence, and export a buyer-ready visual proof packet without wiring API keys.\n\n"
        f"Site: {PUBLIC_SITE_URL}\nRepo: {REPO_URL}"
    )
    hacker_news_title = f"Honeypot Med: local-first prompt-injection proof pages for healthcare AI"
    product_hunt_tagline = "Healthcare AI prompt-injection challenge with badges and proof reports"
    product_hunt_description = (
        "Run healthcare AI trap prompts locally, get a survival score, and export a visual proof dossier, "
        "offline proof PDF, UI mockup, HTML report, README badge, social card, SARIF, JSON, Markdown, and launch copy."
    )
    reddit_title = f"I built Honeypot Med, an open-source prompt-injection honeypot for healthcare AI"
    github_release_blurb = (
        f"{title} produced a {verdict} verdict with {proven} proven findings. "
        "This bundle includes visual proof dossier, offline proof PDF, generated UI mockup, HTML, PDF, SVG social card, "
        "README badge, SARIF, OTEL logs, JSON, Markdown, and launch-kit copy."
    )
    email_subject = f"{title} evidence pack: {verdict} verdict for {source_label}"
    email_body = (
        f"Team,\n\n"
        f"{short_summary}\n"
        f"{evidence_line}\n\n"
        f"Suggested attachments from the bundle:\n"
        f"- proof-dossier.html\n"
        f"- offline-proof.pdf\n"
        f"- ui-mockup.html\n"
        f"- index.html\n"
        f"- summary.pdf\n"
        f"- social-card.svg\n\n"
        f"Project site: {PUBLIC_SITE_URL}\n"
        f"Install and releases: {RELEASES_URL}\n"
        f"Repository: {REPO_URL}\n"
    )
    keywords = [
        "prompt injection healthcare AI",
        "prompt injection honeypot",
        "healthcare AI security",
        "local-first AI security tool",
        "open source prompt security",
        "healthcare LLM red team",
    ]
    faq = [
        {
            "question": "What does Honeypot Med do?",
            "answer": "It inspects suspicious prompts and generates visual proof dossiers, offline proof PDFs, UI mockups, verdict pages, JSON reports, and social cards for healthcare AI workflows.",
        },
        {
            "question": "Does Honeypot Med need API keys?",
            "answer": "No. The default path is local-first and works without API keys.",
        },
        {
            "question": "Why is Honeypot Med shareable?",
            "answer": "Every run exports a public-facing proof bundle with a visual dossier, PDF proof, UI mockup, verdict summary, social card, and launch-ready copy.",
        },
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "headline": headline,
        "summary": short_summary,
        "evidence_line": evidence_line,
        "meta_description": meta_description,
        "x_post": x_post,
        "linkedin_post": linkedin_post,
        "hacker_news_title": hacker_news_title,
        "product_hunt_tagline": product_hunt_tagline,
        "product_hunt_description": product_hunt_description,
        "reddit_title": reddit_title,
        "github_release_blurb": github_release_blurb,
        "email_subject": email_subject,
        "email_body": email_body,
        "keywords": keywords,
        "faq": faq,
        "public_site_url": PUBLIC_SITE_URL,
        "repo_url": REPO_URL,
        "releases_url": RELEASES_URL,
        "install_macos_linux": INSTALL_MACOS_LINUX,
        "install_windows": INSTALL_WINDOWS,
    }


def build_launch_markdown(launch_kit: dict) -> str:
    keywords = ", ".join(launch_kit["keywords"])
    faq_blocks = "\n".join(
        f"### {entry['question']}\n\n{entry['answer']}\n" for entry in launch_kit["faq"]
    )
    sections = [
        "# Honeypot Med Launch Kit",
        "",
        f"- Generated at: {launch_kit['generated_at']}",
        f"- Headline: {launch_kit['headline']}",
        f"- Public site: {launch_kit['public_site_url']}",
        f"- Repo: {launch_kit['repo_url']}",
        "",
        "## Summary",
        "",
        launch_kit["summary"],
        "",
        launch_kit["evidence_line"],
        "",
        "## X Post",
        "",
        launch_kit["x_post"],
        "",
        "## LinkedIn Post",
        "",
        launch_kit["linkedin_post"],
        "",
        "## Hacker News Title",
        "",
        launch_kit["hacker_news_title"],
        "",
        "## Product Hunt",
        "",
        launch_kit["product_hunt_tagline"],
        "",
        launch_kit["product_hunt_description"],
        "",
        "## Reddit Title",
        "",
        launch_kit["reddit_title"],
        "",
        "## GitHub Release Blurb",
        "",
        launch_kit["github_release_blurb"],
        "",
        "## Email Subject",
        "",
        launch_kit["email_subject"],
        "",
        "## Email Body",
        "",
        launch_kit["email_body"],
        "",
        "## Install",
        "",
        f"- Releases page: {launch_kit['releases_url']}",
        f"- macOS / Linux: `{launch_kit['install_macos_linux']}`",
        f"- Windows: `{launch_kit['install_windows']}`",
        "",
        "## Keywords",
        "",
        keywords,
        "",
        "## FAQ",
        "",
        faq_blocks.rstrip(),
        "",
    ]
    return "\n".join(sections)


def build_launch_json(launch_kit: dict) -> str:
    return json.dumps(launch_kit, indent=2) + "\n"
