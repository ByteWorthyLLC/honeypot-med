"""Optional Hugging Face mirror planning without default network access."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .errors import ValidationError


DEFAULT_HF_MIRROR_PLAN = {
    "generated_at": "",
    "default_mode": "plan-only",
    "network_required_for_fetch": True,
    "repos": [
        {
            "repo_id": "neuralchemy/Prompt-injection-dataset",
            "repo_type": "dataset",
            "revision": "main",
            "license_note": "Verify upstream license before redistribution.",
            "transform": "prompt-injection-corpus",
            "fields": {"prompt": "prompt", "label": "label"},
        },
        {
            "repo_id": "wambosec/prompt-injections",
            "repo_type": "dataset",
            "revision": "main",
            "license_note": "Verify upstream license before redistribution.",
            "transform": "prompt-injection-corpus",
            "fields": {"prompt": "text", "label": "label"},
        },
        {
            "repo_id": "TheLumos/MedPI-Dataset",
            "repo_type": "dataset",
            "revision": "main",
            "license_note": "Medical prompt-injection dataset. Verify license and PHI posture.",
            "transform": "medical-prompt-injection",
            "fields": {"prompt": "prompt", "label": "label"},
        },
        {
            "repo_id": "starmpcc/Asclepius-Synthetic-Clinical-Notes",
            "repo_type": "dataset",
            "revision": "main",
            "license_note": "Synthetic clinical notes only. Verify upstream card.",
            "transform": "synthetic-clinical-decoy",
            "fields": {"note": "note"},
        },
        {
            "repo_id": "allenai/wildjailbreak",
            "repo_type": "dataset",
            "revision": "main",
            "license_note": "Use for over-refusal and jailbreak stress tests after license review.",
            "transform": "safety-stress",
            "fields": {"prompt": "prompt"},
        },
    ],
    "local_outputs": [
        "hf-mirror-manifest.json",
        "hf-mirror.md",
        "transformed-pack.json",
    ],
}


def build_hf_mirror_plan() -> dict:
    plan = json.loads(json.dumps(DEFAULT_HF_MIRROR_PLAN))
    plan["generated_at"] = datetime.now(timezone.utc).isoformat()
    return plan


def build_hf_mirror_markdown(plan: dict) -> str:
    lines = [
        "# Honeypot Med Hugging Face Mirror Plan",
        "",
        "This file is a plan, not a download. Honeypot Med does not fetch or upload Hugging Face data unless you explicitly run `hf-mirror fetch`.",
        "",
        "## Candidate Repositories",
        "",
        "| Repo | Type | Transform | Notes |",
        "|---|---|---|---|",
    ]
    for repo in plan["repos"]:
        lines.append(
            f"| `{repo['repo_id']}` | {repo['repo_type']} | `{repo['transform']}` | {repo['license_note']} |"
        )
    lines.extend(
        [
            "",
            "## Suggested Flow",
            "",
            "```bash",
            "python app.py hf-mirror plan --outdir reports/hf-mirror",
            "python app.py hf-mirror fetch --manifest reports/hf-mirror/hf-mirror-manifest.json --outdir data/hf-cache",
            "python app.py hf-mirror transform --input data/local-records.jsonl --outdir reports/hf-pack",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_hf_mirror_plan(outdir: str) -> dict:
    target = Path(outdir)
    target.mkdir(parents=True, exist_ok=True)
    plan = build_hf_mirror_plan()
    manifest_path = target / "hf-mirror-manifest.json"
    readme_path = target / "hf-mirror.md"
    manifest_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    readme_path.write_text(build_hf_mirror_markdown(plan), encoding="utf-8")
    return {"manifest": str(manifest_path), "readme": str(readme_path)}


def fetch_hf_mirror(manifest_path: str, outdir: str) -> dict:
    """Fetch declared repos only when huggingface_hub is installed and user asked for it."""
    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ValidationError("Install huggingface_hub to use hf-mirror fetch, or keep using plan/transform offline.") from exc

    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    target = Path(outdir)
    target.mkdir(parents=True, exist_ok=True)
    downloads = []
    for repo in manifest.get("repos", []):
        repo_id = str(repo["repo_id"])
        local_dir = target / repo_id.replace("/", "__")
        path = snapshot_download(
            repo_id=repo_id,
            repo_type=str(repo.get("repo_type", "dataset")),
            revision=str(repo.get("revision", "main")),
            local_dir=str(local_dir),
        )
        downloads.append({"repo_id": repo_id, "path": path})
    record_path = target / "hf-downloads.json"
    record_path.write_text(json.dumps({"downloads": downloads}, indent=2) + "\n", encoding="utf-8")
    return {"downloads": downloads, "record": str(record_path)}


def transform_jsonl_to_pack(input_path: str, outdir: str, *, title: str = "HF Mirror Local Pack") -> dict:
    """Transform local JSONL rows into a Honeypot Med pack without assuming a remote schema."""
    source = Path(input_path)
    events = []
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        raw = json.loads(line)
        if not isinstance(raw, dict):
            continue
        prompt = raw.get("prompt") or raw.get("text") or raw.get("input") or raw.get("question")
        if not prompt:
            continue
        events.append(
            {
                "prompt": str(prompt),
                "tool_calls": [],
                "model_output": str(raw.get("model_output", raw.get("output", ""))),
                "response": str(raw.get("response", "")),
                "metadata": {"source_line": line_number, "hf_transform": True},
            }
        )
    if not events:
        raise ValidationError("No prompt-like rows found in input JSONL.")

    target = Path(outdir)
    target.mkdir(parents=True, exist_ok=True)
    pack_path = target / "transformed-pack.json"
    pack = {"title": title, "events": events}
    pack_path.write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")
    return {"pack": str(pack_path), "event_count": len(events)}
