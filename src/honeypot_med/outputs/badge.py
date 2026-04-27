"""SVG badge helpers for README and public report embeds."""

from __future__ import annotations

from html import escape


def _status_color(verdict: str) -> str:
    normalized = verdict.lower()
    if normalized in {"pass", "survived", "complete"}:
        return "#257354"
    if normalized in {"review", "needs-work"}:
        return "#b66a16"
    return "#b02719"


def build_badge_svg(*, label: str, value: str, verdict: str) -> str:
    """Build a static, dependency-free SVG badge."""
    left_width = max(102, len(label) * 7 + 28)
    right_width = max(96, len(value) * 7 + 28)
    total_width = left_width + right_width
    color = _status_color(verdict)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="28" viewBox="0 0 {total_width} 28" role="img" aria-label="{escape(label)}: {escape(value)}">
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#fff" stop-opacity=".16"/>
    <stop offset="1" stop-color="#000" stop-opacity=".08"/>
  </linearGradient>
  <rect width="{total_width}" height="28" rx="8" fill="#1f2630"/>
  <rect x="{left_width}" width="{right_width}" height="28" rx="8" fill="{color}"/>
  <rect width="{total_width}" height="28" rx="8" fill="url(#s)"/>
  <text x="{left_width / 2:.1f}" y="18" text-anchor="middle" font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" font-size="12" font-weight="700" fill="#fff">{escape(label)}</text>
  <text x="{left_width + right_width / 2:.1f}" y="18" text-anchor="middle" font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" font-size="12" font-weight="800" fill="#fff">{escape(value)}</text>
</svg>
"""


def badge_value_for_report(report: dict) -> tuple[str, str]:
    challenge = report.get("challenge")
    if isinstance(challenge, dict):
        return str(challenge.get("score_label", "0/0 survived")), str(challenge.get("verdict", "review"))

    severity = report.get("severity_counts", {})
    if int(severity.get("critical", 0)) > 0 or int(severity.get("high", 0)) > 0:
        return f"{int(report.get('high_risk_count', 0))} high-risk", "block"
    if int(severity.get("medium", 0)) > 0:
        return "review", "review"
    return "pass", "pass"


def build_report_badge_svg(report: dict) -> str:
    value, verdict = badge_value_for_report(report)
    return build_badge_svg(label="Honeypot Med", value=value, verdict=verdict)


def build_badge_markdown(*, report_url: str = "index.html", badge_path: str = "badge.svg") -> str:
    return f"[![Honeypot Med result]({badge_path})]({report_url})\n"
