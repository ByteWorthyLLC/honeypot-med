"""Launch-readiness checks for the local Honeypot Med repository."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_FILES = {
    "governance": [
        "LICENSE",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "CHANGELOG.md",
        ".github/PULL_REQUEST_TEMPLATE.md",
    ],
    "automation": [
        ".github/workflows/ci.yml",
        ".github/workflows/codeql.yml",
        ".github/workflows/container.yml",
        ".github/workflows/pages.yml",
        ".github/workflows/package.yml",
        "action.yml",
    ],
    "runtime": [
        "app.py",
        "run.sh",
        "run.ps1",
        "run.bat",
        "Dockerfile",
        "docker-compose.yml",
        "pyproject.toml",
    ],
    "public_site": [
        "site/index.html",
        "site/faq/index.html",
        "site/challenge/index.html",
        "site/reports/index.html",
        "site/integrations/index.html",
        "site/launch-room/index.html",
        "site/media/index.html",
        "site/readiness/index.html",
        "site/releases/index.html",
        "site/llms.txt",
        "site/sitemap.xml",
        "site/robots.txt",
    ],
    "sample_visual_packet": [
        "site/reports/healthcare-challenge/index.html",
        "site/reports/healthcare-challenge/proof-dossier.html",
        "site/reports/healthcare-challenge/offline-proof.pdf",
        "site/reports/healthcare-challenge/ui-mockup.html",
        "site/reports/healthcare-challenge/social-card.svg",
        "site/reports/healthcare-challenge/social-card.png",
        "site/reports/healthcare-challenge/badge.svg",
        "site/reports/healthcare-challenge/badge.png",
        "site/reports/healthcare-challenge/bundle.json",
        "site/reports/healthcare-challenge/report.json",
        "site/reports/healthcare-challenge/report.md",
        "site/reports/healthcare-challenge/honeypot-med.sarif",
        "site/reports/healthcare-challenge/honeypot-med.junit.xml",
        "site/reports/healthcare-challenge/otel-logs.json",
        "site/reports/healthcare-challenge/eval-kit-manifest.json",
        "site/reports/healthcare-challenge/hf-artifact-manifest.md",
    ],
}

REQUIRED_TEXT = {
    "README.md": [
        "No API keys are required",
        "visual proof dossier",
        "offline proof PDF",
        "UI mockup",
    ],
    "docs/self-hosting.md": [
        "No backend is required for normal usage",
        "no paid backend dependency required",
    ],
    "site/index.html": [
        "visual proof dossier",
        "offline proof PDF",
        "UI mockup",
    ],
    "site/faq/index.html": [
        "No. The intended default path is local-first",
        "visual proof dossier",
    ],
    "site/readiness/index.html": [
        "Launch state should be measurable",
        "python app.py readiness --strict",
    ],
}

FORBIDDEN_TERMS = [
    "leader" + "board",
    "leader" + " board",
    "score" + "board",
    "score" + " board",
    "leader" + "board-row",
    "rank" + "ing",
    "rank" + "ed",
    "rank" + "ings",
    "hf " + "row",
    "public " + "comparison",
    "comparison" + "-table",
    "comparison " + "table",
    "top " + "score",
    "win" + "ner",
]

TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".svg",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _check_file(root: Path, section: str, rel_path: str) -> dict:
    path = root / rel_path
    return {
        "id": f"{section}:{rel_path}",
        "section": section,
        "label": rel_path,
        "path": rel_path,
        "status": "pass" if path.exists() and path.is_file() else "fail",
        "detail": "present" if path.exists() and path.is_file() else "missing",
    }


def _check_required_text(root: Path) -> list[dict]:
    checks: list[dict] = []
    for rel_path, needles in REQUIRED_TEXT.items():
        path = root / rel_path
        if not path.exists():
            for needle in needles:
                checks.append(
                    {
                        "id": f"text:{rel_path}:{needle}",
                        "section": "copy",
                        "label": f"{rel_path} contains {needle}",
                        "path": rel_path,
                        "status": "fail",
                        "detail": "file missing",
                    }
                )
            continue

        text = path.read_text(encoding="utf-8", errors="replace")
        for needle in needles:
            present = needle in text
            checks.append(
                {
                    "id": f"text:{rel_path}:{needle}",
                    "section": "copy",
                    "label": f"{rel_path} contains {needle}",
                    "path": rel_path,
                    "status": "pass" if present else "fail",
                    "detail": "present" if present else "missing",
                }
            )
    return checks


def _iter_text_files(root: Path) -> list[Path]:
    ignored_parts = {".git", ".venv", "__pycache__", ".mypy_cache", ".pytest_cache"}
    results: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part in ignored_parts for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if path.stat().st_size > 1_000_000:
            continue
        results.append(path)
    return results


def _check_forbidden_terms(root: Path) -> list[dict]:
    hits: list[str] = []
    for path in _iter_text_files(root):
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        for term in FORBIDDEN_TERMS:
            if term in text:
                hits.append(f"{_rel(path, root)}:{term}")
    return [
        {
            "id": "copy:no-vanity-surface-terms",
            "section": "copy",
            "label": "No public vanity artifacts or copy",
            "path": ".",
            "status": "pass" if not hits else "fail",
            "detail": "clean" if not hits else ", ".join(hits[:10]),
        }
    ]


def build_readiness_report(root: str | Path) -> dict:
    repo_root = Path(root).expanduser().resolve()
    checks: list[dict] = []
    for section, paths in REQUIRED_FILES.items():
        for rel_path in paths:
            checks.append(_check_file(repo_root, section, rel_path))
    checks.extend(_check_required_text(repo_root))
    checks.extend(_check_forbidden_terms(repo_root))

    passed = sum(1 for check in checks if check["status"] == "pass")
    failed = len(checks) - passed
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(repo_root),
        "status": "pass" if failed == 0 else "fail",
        "summary": {
            "passed": passed,
            "failed": failed,
            "total": len(checks),
        },
        "checks": checks,
    }


def build_readiness_markdown(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# Honeypot Med Launch Readiness",
        "",
        f"- Status: **{str(report['status']).upper()}**",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        f"- Total checks: {summary['total']}",
        f"- Generated: {report['generated_at']}",
        f"- Root: `{report['root']}`",
        "",
        "## Checks",
        "",
        "| Status | Section | Check | Detail |",
        "|---|---|---|---|",
    ]
    for check in report["checks"]:
        status = "PASS" if check["status"] == "pass" else "FAIL"
        label = str(check["label"]).replace("|", "\\|")
        detail = str(check["detail"]).replace("|", "\\|")
        lines.append(f"| {status} | {check['section']} | {label} | {detail} |")
    lines.append("")
    return "\n".join(lines)


def write_readiness_artifacts(root: str | Path, outdir: str | Path) -> dict:
    target = Path(outdir).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    report = build_readiness_report(root)
    json_path = target / "launch-readiness.json"
    markdown_path = target / "launch-readiness.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(build_readiness_markdown(report), encoding="utf-8")
    return {
        "status": report["status"],
        "summary": report["summary"],
        "json": str(json_path),
        "markdown": str(markdown_path),
        "report": report,
    }
