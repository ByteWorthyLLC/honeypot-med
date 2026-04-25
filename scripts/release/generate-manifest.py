#!/usr/bin/env python3
"""Generate release checksums and a machine-readable artifact manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import honeypot_med  # noqa: E402


EXCLUDED_NAMES = {"SHA256SUMS.txt", "release-manifest.json"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _platform_for_path(path: Path) -> str:
    parts = path.parts
    if parts and parts[0] in {"linux", "macos", "windows"}:
        return parts[0]
    return "root"


def build_manifest(dist_dir: Path) -> dict:
    artifacts = []
    for file_path in sorted(path for path in dist_dir.rglob("*") if path.is_file()):
        rel_path = file_path.relative_to(dist_dir)
        if rel_path.name in EXCLUDED_NAMES:
            continue
        artifacts.append(
            {
                "path": rel_path.as_posix(),
                "platform": _platform_for_path(rel_path),
                "size_bytes": file_path.stat().st_size,
                "sha256": _sha256(file_path),
            }
        )

    return {
        "project": "honeypot-med",
        "version": honeypot_med.__version__,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }


def write_outputs(manifest: dict, *, json_path: Path, sha_path: Path) -> None:
    json_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    lines = [f"{artifact['sha256']}  {artifact['path']}" for artifact in manifest["artifacts"]]
    sha_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate honeypot-med release manifest files.")
    parser.add_argument("--dist-dir", default=str(ROOT / "dist"))
    parser.add_argument("--output-json", default=None)
    parser.add_argument("--output-sha256", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dist_dir = Path(args.dist_dir).resolve()
    if not dist_dir.exists() or not dist_dir.is_dir():
        print(f"dist directory not found: {dist_dir}", file=sys.stderr)
        return 4

    json_path = Path(args.output_json).resolve() if args.output_json else dist_dir / "release-manifest.json"
    sha_path = Path(args.output_sha256).resolve() if args.output_sha256 else dist_dir / "SHA256SUMS.txt"

    manifest = build_manifest(dist_dir)
    write_outputs(manifest, json_path=json_path, sha_path=sha_path)

    print(f"wrote manifest: {json_path}")
    print(f"wrote checksums: {sha_path}")
    print(f"artifacts indexed: {manifest['artifact_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

