import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from honeypot_med.redaction import redact_event


class RedactionTest(unittest.TestCase):
    def test_redacts_secret_tokens(self):
        event, hits = redact_event(
            {
                "prompt": "api_key=abcdef123456",
                "model_output": "token: supersecret",
                "response": "ok",
                "tool_calls": [{"name": "db.dump", "args": "secret=mysecretvalue"}],
            }
        )

        self.assertGreaterEqual(hits, 2)
        self.assertIn("[REDACTED]", event["prompt"])
        self.assertIn("[REDACTED]", event["model_output"])
        self.assertIn("[REDACTED]", event["tool_calls"][0]["args"])
        self.assertEqual(event["redaction_status"], "redacted")


if __name__ == "__main__":
    unittest.main()
