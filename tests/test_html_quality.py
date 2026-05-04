"""HTML quality and ecosystem validation for the static site."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

REQUIRED_META = ["<meta charset", "<meta name=\"viewport"]
ECOSYSTEM_PROJECTS = ["outbreaktinder", "vqol", "hightimized", "sovra"]

# Generated proof artifacts have minimal footers — skip ecosystem checks
GENERATED_REPORT_DIRS = {"reports/healthcare-challenge"}


def _collect_html_files():
    return sorted(SITE.rglob("*.html"))


class HtmlStructureTest(unittest.TestCase):
    """Every HTML file must have valid structure."""

    def test_all_html_files_have_doctype(self):
        for path in _collect_html_files():
            content = path.read_text(encoding="utf-8")
            rel = path.relative_to(SITE)
            self.assertTrue(
                content.strip().lower().startswith("<!doctype html"),
                f"{rel} missing <!doctype html>",
            )

    def test_all_html_files_have_lang_attribute(self):
        for path in _collect_html_files():
            content = path.read_text(encoding="utf-8")
            rel = path.relative_to(SITE)
            self.assertRegex(
                content,
                r'<html[^>]*\slang="[a-z]{2}"',
                f"{rel} missing lang attribute on <html>",
            )

    def test_all_html_files_have_charset_and_viewport(self):
        for path in _collect_html_files():
            content = path.read_text(encoding="utf-8").lower()
            rel = path.relative_to(SITE)
            for meta in REQUIRED_META:
                self.assertIn(
                    meta.lower(),
                    content,
                    f"{rel} missing {meta}",
                )

    def test_all_html_files_have_title(self):
        for path in _collect_html_files():
            content = path.read_text(encoding="utf-8")
            rel = path.relative_to(SITE)
            self.assertRegex(
                content,
                r"<title>[^<]+</title>",
                f"{rel} missing or empty <title>",
            )

    def test_no_broken_internal_links(self):
        """Check that href values pointing to local paths resolve to existing files."""
        link_re = re.compile(r'href="(/[^"#?]*)"')
        broken = []
        for path in _collect_html_files():
            content = path.read_text(encoding="utf-8")
            rel = path.relative_to(SITE)
            for match in link_re.finditer(content):
                href = match.group(1)
                target = SITE / href.lstrip("/")
                if target.is_dir():
                    target = target / "index.html"
                if not target.exists():
                    broken.append(f"{rel} → {href}")
        if broken:
            self.fail(f"Broken internal links:\n" + "\n".join(broken[:20]))


class EcosystemFooterTest(unittest.TestCase):
    """Every page with a <footer> must contain ecosystem cross-links."""

    def test_homepage_has_ecosystem_section(self):
        html = (SITE / "index.html").read_text(encoding="utf-8")
        self.assertIn("More from ByteWorthy", html)
        for project in ECOSYSTEM_PROJECTS:
            self.assertIn(project, html, f"Homepage missing ecosystem link: {project}")

    def test_subpages_have_ecosystem_section(self):
        missing = []
        for path in _collect_html_files():
            if path.name == "404.html":
                continue
            rel = path.relative_to(SITE)
            if any(str(rel).startswith(d) for d in GENERATED_REPORT_DIRS):
                continue
            content = path.read_text(encoding="utf-8")
            if "<footer" not in content:
                continue
            if "footer-ecosystem" not in content and "More from ByteWorthy" not in content:
                missing.append(str(rel))
        if missing:
            self.fail(
                f"{len(missing)} pages with <footer> missing ecosystem section:\n"
                + "\n".join(missing[:10])
            )


if __name__ == "__main__":
    unittest.main()
