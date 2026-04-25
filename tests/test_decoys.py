import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from honeypot_med.decoys import load_decoy_pack


class DecoyPackTest(unittest.TestCase):
    def test_load_decoy_pack(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "decoys.json"
            payload = {
                "decoys": [
                    {
                        "path": "/decoy/claims/export",
                        "tool_name": "claims.export",
                        "source": "decoy.claims.export",
                        "default_prompt": "Claims export request",
                        "response": {"status": "ok", "rows": 0},
                    }
                ]
            }
            path.write_text(json.dumps(payload), encoding="utf-8")

            routes = load_decoy_pack(path)
            self.assertEqual(len(routes), 1)
            self.assertEqual(routes[0].path, "/decoy/claims/export")
            self.assertEqual(routes[0].tool_name, "claims.export")


if __name__ == "__main__":
    unittest.main()
