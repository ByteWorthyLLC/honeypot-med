"""Local release bundle builder for generated report directories."""

from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_release_bundle(source_dir: str, outdir: str, *, name: str) -> dict:
    source = Path(source_dir)
    target = Path(outdir)
    if not source.is_dir():
        raise ValueError(f"Release source directory does not exist: {source}")
    target.mkdir(parents=True, exist_ok=True)

    zip_path = target / f"{name}.zip"
    manifest_path = target / f"{name}.manifest.json"
    checksums_path = target / f"{name}.sha256"
    notes_path = target / f"{name}.release-notes.md"

    files = [path for path in sorted(source.rglob("*")) if path.is_file()]
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(source))

    zip_sha = _sha256(zip_path)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "name": name,
        "source_dir": str(source),
        "zip": zip_path.name,
        "zip_sha256": zip_sha,
        "file_count": len(files),
        "files": [
            {
                "path": str(path.relative_to(source)),
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for path in files
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    checksums_path.write_text(f"{zip_sha}  {zip_path.name}\n", encoding="utf-8")
    notes_path.write_text(
        "\n".join(
            [
                f"# {name} Release Bundle",
                "",
                f"- Source directory: `{source}`",
                f"- Archive: `{zip_path.name}`",
                f"- SHA-256: `{zip_sha}`",
                f"- Files included: {len(files)}",
                "",
                "This bundle is generated locally by Honeypot Med and is suitable for attaching to a GitHub Release.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {
        "zip": str(zip_path),
        "manifest": str(manifest_path),
        "sha256": str(checksums_path),
        "release_notes": str(notes_path),
    }
