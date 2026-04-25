import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from honeypot_med.runtime import enrich_report_with_engine, load_runtime_config, save_runtime_config


class RuntimeTest(unittest.TestCase):
    def test_runtime_config_round_trip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.json"
            save_runtime_config(
                {
                    "engine_mode": "local",
                    "asset_dir": str(Path(tmpdir) / "a"),
                    "store_path": str(Path(tmpdir) / "d" / "events.jsonl"),
                    "audit_log_path": str(Path(tmpdir) / "logs" / "audit.jsonl"),
                    "remote_timeout_sec": 7,
                    "remote_retries": 2,
                },
                str(path),
            )
            config, loaded_path = load_runtime_config(str(path))
            self.assertEqual(str(loaded_path), str(path))
            self.assertEqual(config["engine_mode"], "local")
            self.assertEqual(config["remote_timeout_sec"], 7)
            self.assertEqual(config["remote_retries"], 2)

    def test_engine_enrichment_local(self):
        report = {
            "policy": {"min_high_risk": 60},
            "events": [{"severity": "low", "risk_score": 10, "finding_count": 0}],
            "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 1},
            "high_risk_count": 0,
        }
        payload = {"events": [{"prompt": "hello"}]}
        enriched = enrich_report_with_engine(
            report,
            payload,
            mode="local",
            remote_url=None,
            remote_auth_token=None,
            allow_network=False,
        )
        self.assertIn("engine", enriched)
        self.assertEqual(enriched["engine"]["selected_mode"], "local")


if __name__ == "__main__":
    unittest.main()
