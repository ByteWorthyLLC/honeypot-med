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
        self.assertTrue((SITE / "daily" / "index.html").exists())
        self.assertTrue((SITE / "ctf" / "index.html").exists())
        self.assertTrue((SITE / "casebook" / "index.html").exists())
        self.assertTrue((SITE / "codex" / "index.html").exists())
        self.assertTrue((SITE / "field-notes" / "index.html").exists())
        self.assertTrue((SITE / "gallery" / "index.html").exists())
        self.assertTrue((SITE / "launch-room" / "index.html").exists())
        self.assertTrue((SITE / "media" / "index.html").exists())
        self.assertTrue((SITE / "readiness" / "index.html").exists())
        self.assertTrue((SITE / "reports" / "index.html").exists())
        self.assertTrue((SITE / "integrations" / "index.html").exists())
        self.assertTrue((SITE / "hf-lab" / "index.html").exists())
        self.assertTrue((SITE / "contribute" / "index.html").exists())
        self.assertTrue((SITE / "releases" / "index.html").exists())

    def test_homepage_contains_metadata_and_calls_to_action(self):
        html = (SITE / "index.html").read_text(encoding="utf-8")
        self.assertIn("application/ld+json", html)
        self.assertIn("visual proof dossier", html)
        self.assertIn("offline proof PDF", html)
        self.assertIn("UI mockup", html)
        self.assertIn("Challenge mode", html)
        self.assertIn("Every boring finding gets a monster name", html)
        self.assertIn("Inquiry mode", html)
        self.assertIn("counterfactual prompts", html)
        self.assertIn("daily dungeon", html)
        self.assertIn("prompt CTF", html)
        self.assertIn("redacted casebook", html)
        self.assertIn("OpenInference traces", html)
        self.assertIn("Hugging Face cards", html)
        self.assertIn("eval kit", html)
        self.assertIn("Launch Room", html)
        self.assertIn("Evidence gallery", html)
        self.assertIn("OWASP LLM01", html)
        self.assertIn("Steal these angles", html)
        self.assertIn("Open GitHub", html)
        self.assertIn("Open releases", html)
        self.assertIn("Public pulse counters", html)
        self.assertIn("Media kit", html)
        self.assertIn("Readiness Check", html)

    def test_subpages_exist(self):
        self.assertTrue((SITE / "faq" / "index.html").exists())
        self.assertTrue((SITE / "challenge" / "index.html").exists())
        self.assertTrue((SITE / "daily" / "index.html").exists())
        self.assertTrue((SITE / "ctf" / "index.html").exists())
        self.assertTrue((SITE / "casebook" / "index.html").exists())
        self.assertTrue((SITE / "codex" / "index.html").exists())
        self.assertTrue((SITE / "field-notes" / "index.html").exists())
        self.assertTrue((SITE / "gallery" / "index.html").exists())
        self.assertTrue((SITE / "launch-room" / "index.html").exists())
        self.assertTrue((SITE / "readiness" / "index.html").exists())
        self.assertTrue((SITE / "reports" / "index.html").exists())
        self.assertTrue((SITE / "integrations" / "index.html").exists())
        self.assertTrue((SITE / "hf-lab" / "index.html").exists())
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
        # Pin the action by name; tolerate dependabot major version bumps.
        # We assert the SARIF upload step exists, not its exact pinned version.
        self.assertIn("github/codeql-action/upload-sarif@v", action)
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
        self.assertIn("casebook.html", reports)
        self.assertIn("honeypot-med.junit.xml", reports)
        self.assertIn("openinference-traces.jsonl", reports)
        self.assertIn("proof-dossier.html", reports)
        self.assertIn("offline-proof.pdf", reports)
        self.assertIn("ui-mockup.html", reports)

    def test_new_curiosity_surfaces_and_report_artifacts_exist(self):
        report = SITE / "reports" / "healthcare-challenge"
        for name in [
            "casebook.html",
            "casebook-xray.html",
            "casebook-ledger.html",
            "traparium.html",
            "unknowns.html",
            "failure-recipes.md",
            "trap-tree.svg",
            "lab-notebook.ipynb",
            "flags.json",
            "hints.html",
            "writeup.md",
            "honeypot-med.junit.xml",
            "github-summary.md",
            "proof-dossier.html",
            "offline-proof.pdf",
            "ui-mockup.html",
            "social-card.png",
            "badge.png",
            "openinference-traces.jsonl",
            "langsmith-runs.jsonl",
            "otel-collector.yaml",
            "README.dataset-card.md",
            "system-card.md",
            "hf-artifact-manifest.md",
        ]:
            self.assertTrue((report / name).exists(), msg=name)

        casebook = (SITE / "casebook" / "index.html").read_text(encoding="utf-8")
        self.assertIn("The report becomes a case file.", casebook)
        daily = (SITE / "daily" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Every day gets a dungeon.", daily)
        ctf = (SITE / "ctf" / "index.html").read_text(encoding="utf-8")
        self.assertIn("The flags are predicates, not secrets.", ctf)
        hf_lab = (SITE / "hf-lab" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Hugging Face as a lab bench", hf_lab)
        readiness = (SITE / "readiness" / "index.html").read_text(encoding="utf-8")
        self.assertIn("python app.py readiness --strict", readiness)
        self.assertIn("Launch state should be measurable", readiness)


if __name__ == "__main__":
    unittest.main()
