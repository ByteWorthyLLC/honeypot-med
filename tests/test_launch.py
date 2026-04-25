import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from honeypot_med import cli


class LaunchBehaviorTest(unittest.TestCase):
    def test_no_args_defaults_to_launch(self):
        with mock.patch("honeypot_med.cli.run_studio_server") as run_studio_server:
            exit_code = cli.main([])
        self.assertEqual(exit_code, 0)
        run_studio_server.assert_called_once()

    def test_launch_command_runs_without_keys(self):
        with mock.patch("honeypot_med.cli.run_studio_server") as run_studio_server:
            exit_code = cli.main(["launch", "--no-open-browser"])
        self.assertEqual(exit_code, 0)
        _, kwargs = run_studio_server.call_args
        self.assertEqual(kwargs["config"]["engine_mode"], "auto")
        self.assertFalse(bool(kwargs["config"].get("remote_auth_token")))


if __name__ == "__main__":
    unittest.main()
