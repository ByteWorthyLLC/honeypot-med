import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseManifestTest(unittest.TestCase):
    def _load_module(self):
        script_path = ROOT / "scripts" / "release" / "generate-manifest.py"
        spec = importlib.util.spec_from_file_location("honeypot_med_release_manifest", script_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def test_build_manifest_indexes_artifacts(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_dir = Path(tmpdir)
            linux_dir = dist_dir / "linux"
            linux_dir.mkdir()
            artifact = linux_dir / "honeypot-med.tar.gz"
            artifact.write_bytes(b"artifact-bytes")

            manifest = module.build_manifest(dist_dir)

        self.assertEqual(manifest["artifact_count"], 1)
        self.assertEqual(manifest["artifacts"][0]["path"], "linux/honeypot-med.tar.gz")
        self.assertEqual(manifest["artifacts"][0]["platform"], "linux")
        self.assertTrue(manifest["artifacts"][0]["sha256"])

    def test_write_outputs_creates_json_and_checksum_files(self):
        module = self._load_module()
        manifest = {
            "project": "honeypot-med",
            "version": "0.4.0",
            "generated_at": "2026-04-24T00:00:00+00:00",
            "artifact_count": 1,
            "artifacts": [
                {
                    "path": "linux/honeypot-med.tar.gz",
                    "platform": "linux",
                    "size_bytes": 12,
                    "sha256": "abc123",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "release-manifest.json"
            sha_path = Path(tmpdir) / "SHA256SUMS.txt"
            module.write_outputs(manifest, json_path=json_path, sha_path=sha_path)

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            sha_text = sha_path.read_text(encoding="utf-8")

        self.assertEqual(payload["artifact_count"], 1)
        self.assertIn("abc123  linux/honeypot-med.tar.gz", sha_text)


if __name__ == "__main__":
    unittest.main()
