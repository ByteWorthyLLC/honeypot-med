import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from honeypot_med.store import JSONLStore


class StoreTest(unittest.TestCase):
    def test_append_and_read_round_trip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "events.jsonl"
            store = JSONLStore(path)
            store.append({"event_id": "evt-1", "prompt": "hello"})
            store.append({"event_id": "evt-2", "prompt": "world"})

            rows = store.read_all()
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["event_id"], "evt-1")
            self.assertEqual(rows[1]["event_id"], "evt-2")

    def test_split_by_age(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "events.jsonl"
            store = JSONLStore(path)
            old_ts = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
            new_ts = datetime.now(timezone.utc).isoformat()
            store.append({"event_id": "old", "captured_at": old_ts})
            store.append({"event_id": "new", "captured_at": new_ts})

            purged, kept = store.split_by_age(30)
            self.assertEqual(len(purged), 1)
            self.assertEqual(len(kept), 1)


if __name__ == "__main__":
    unittest.main()
