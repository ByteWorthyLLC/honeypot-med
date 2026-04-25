import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class SiteSurfaceTest(unittest.TestCase):
    def test_site_search_artifacts_exist(self):
        self.assertTrue((SITE / "index.html").exists())
        self.assertTrue((SITE / "robots.txt").exists())
        self.assertTrue((SITE / "sitemap.xml").exists())
        self.assertTrue((SITE / "llms.txt").exists())
        self.assertTrue((SITE / "site.webmanifest").exists())
        self.assertTrue((SITE / "media" / "index.html").exists())

    def test_homepage_contains_metadata_and_calls_to_action(self):
        html = (SITE / "index.html").read_text(encoding="utf-8")
        self.assertIn("application/ld+json", html)
        self.assertIn("Prompt-injection proof pages for healthcare AI.", html)
        self.assertIn("Steal these angles", html)
        self.assertIn("Open GitHub", html)
        self.assertIn("Public pulse counters", html)
        self.assertIn("Media kit", html)

    def test_subpages_exist(self):
        self.assertTrue((SITE / "faq" / "index.html").exists())
        self.assertTrue((SITE / "use-cases" / "healthcare-ai" / "index.html").exists())
        self.assertTrue((SITE / "use-cases" / "claims-automation" / "index.html").exists())
        self.assertTrue((SITE / "use-cases" / "patient-triage" / "index.html").exists())
        self.assertTrue((SITE / "compare" / "prompt-guardrails-vs-honeypots" / "index.html").exists())
        self.assertTrue((SITE / "compare" / "honeypot-med-vs-generic-red-team-report" / "index.html").exists())

    def test_app_js_contains_counter_tracking(self):
        script = (SITE / "assets" / "app.js").read_text(encoding="utf-8")
        self.assertIn("api.github.com/repos/ByteWorthyLLC/honeypot-med", script)
        self.assertIn("data-repo-metric", script)


if __name__ == "__main__":
    unittest.main()
