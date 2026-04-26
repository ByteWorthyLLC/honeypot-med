import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class SiteSurfaceTest(unittest.TestCase):
    def test_site_search_artifacts_exist(self):
        self.assertTrue((SITE / "index.html").exists())
        self.assertTrue((SITE / "404.html").exists())
        self.assertTrue((SITE / "robots.txt").exists())
        self.assertTrue((SITE / "sitemap.xml").exists())
        self.assertTrue((SITE / "llms.txt").exists())
        self.assertTrue((SITE / "site.webmanifest").exists())
        self.assertTrue((SITE / "challenge" / "index.html").exists())
        self.assertTrue((SITE / "codex" / "index.html").exists())
        self.assertTrue((SITE / "field-notes" / "index.html").exists())
        self.assertTrue((SITE / "gallery" / "index.html").exists())
        self.assertTrue((SITE / "launch-room" / "index.html").exists())
        self.assertTrue((SITE / "media" / "index.html").exists())
        self.assertTrue((SITE / "reports" / "index.html").exists())
        self.assertTrue((SITE / "integrations" / "index.html").exists())
        self.assertTrue((SITE / "contribute" / "index.html").exists())
        self.assertTrue((SITE / "releases" / "index.html").exists())

    def test_homepage_contains_metadata_and_calls_to_action(self):
        html = (SITE / "index.html").read_text(encoding="utf-8")
        self.assertIn("application/ld+json", html)
        self.assertIn("Prompt-injection proof pages for healthcare AI.", html)
        self.assertIn("Can your healthcare AI survive 10 traps?", html)
        self.assertIn("Challenge mode", html)
        self.assertIn("Every boring finding gets a monster name", html)
        self.assertIn("Promotion is optional. Questions are the product.", html)
        self.assertIn("counterfactual prompts", html)
        self.assertIn("eval kit", html)
        self.assertIn("Launch Room", html)
        self.assertIn("Evidence gallery", html)
        self.assertIn("OWASP LLM01", html)
        self.assertIn("Steal these angles", html)
        self.assertIn("Open GitHub", html)
        self.assertIn("Open releases", html)
        self.assertIn("Public pulse counters", html)
        self.assertIn("Media kit", html)

    def test_subpages_exist(self):
        self.assertTrue((SITE / "faq" / "index.html").exists())
        self.assertTrue((SITE / "challenge" / "index.html").exists())
        self.assertTrue((SITE / "codex" / "index.html").exists())
        self.assertTrue((SITE / "field-notes" / "index.html").exists())
        self.assertTrue((SITE / "gallery" / "index.html").exists())
        self.assertTrue((SITE / "launch-room" / "index.html").exists())
        self.assertTrue((SITE / "reports" / "index.html").exists())
        self.assertTrue((SITE / "integrations" / "index.html").exists())
        self.assertTrue((SITE / "contribute" / "index.html").exists())
        self.assertTrue((SITE / "use-cases" / "healthcare-ai" / "index.html").exists())
        self.assertTrue((SITE / "use-cases" / "claims-automation" / "index.html").exists())
        self.assertTrue((SITE / "use-cases" / "prior-authorization" / "index.html").exists())
        self.assertTrue((SITE / "use-cases" / "patient-triage" / "index.html").exists())
        self.assertTrue((SITE / "compare" / "prompt-guardrails-vs-honeypots" / "index.html").exists())
        self.assertTrue((SITE / "compare" / "guardrails-vs-launch-review" / "index.html").exists())
        self.assertTrue((SITE / "compare" / "evals-vs-proof-bundles" / "index.html").exists())
        self.assertTrue((SITE / "compare" / "honeypot-med-vs-generic-red-team-report" / "index.html").exists())

    def test_app_js_contains_counter_tracking(self):
        script = (SITE / "assets" / "app.js").read_text(encoding="utf-8")
        self.assertIn("api.github.com/repos/ByteWorthyLLC/honeypot-med", script)
        self.assertIn("GITHUB_RELEASE_API", script)
        self.assertIn("/releases/latest", script)
        self.assertIn("data-repo-metric", script)

    def test_launch_kit_and_action_surfaces_exist(self):
        launch_kit = json.loads((SITE / "launch-kit.json").read_text(encoding="utf-8"))
        self.assertIn("Product Hunt", {channel["channel"] for channel in launch_kit["channels"]})
        self.assertIn("Show HN", {channel["channel"] for channel in launch_kit["channels"]})
        action = (ROOT / "action.yml").read_text(encoding="utf-8")
        self.assertIn("github/codeql-action/upload-sarif@v3", action)
        self.assertIn("honeypot-med challenge", action)

    def test_curiosity_and_eval_surfaces_are_linked(self):
        field_notes = (SITE / "field-notes" / "index.html").read_text(encoding="utf-8")
        self.assertIn("counterfactual prompt decks", field_notes)
        self.assertIn("python app.py experiment", field_notes)
        integrations = (SITE / "integrations" / "index.html").read_text(encoding="utf-8")
        self.assertIn("python app.py eval-kit", integrations)
        self.assertIn("promptfoo", integrations)
        reports = (SITE / "reports" / "index.html").read_text(encoding="utf-8")
        self.assertIn("experiment-plan.md", reports)
        self.assertIn("eval-kit.md", reports)


if __name__ == "__main__":
    unittest.main()
