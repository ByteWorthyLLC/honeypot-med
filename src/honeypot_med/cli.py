"""CLI entrypoint for prompt injection honeypot analysis and capture."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from .attack_packs import describe_attack_pack, list_attack_packs, load_attack_pack_payload
from .audit import append_audit_event
from .baseline import apply_suppressions, load_suppressions
from .challenge import DEFAULT_CHALLENGE_PACK, write_challenge_bundle
from .decoys import load_decoy_pack
from .eval_adapters import write_eval_adapter_artifacts
from .errors import ValidationError
from .events import events_to_payload, normalize_event
from .experiments import write_experiment_artifacts
from .exports import write_share_bundle
from .inquiry import write_inquiry_artifacts
from .lab import write_lab_artifacts
from .models import InputPayload
from .outputs.badge import build_badge_markdown, build_report_badge_svg
from .outputs.otel import report_to_otel_logs
from .outputs.sarif import report_to_sarif
from .redaction import redact_event
from .runtime import (
    check_network,
    ensure_runtime_dirs,
    enrich_report_with_engine,
    load_runtime_config,
    save_runtime_config,
)
from .server import run_server
from .service import DEFAULT_RULES, analyze_prompts
from .studio import run_studio_server
from .store import JSONLStore

LOGGER = logging.getLogger("honeypot_med")

EXIT_OK = 0
EXIT_GENERIC_ERROR = 1
EXIT_VALIDATION_ERROR = 2
EXIT_FILE_ERROR = 4
EXIT_JSON_ERROR = 5
EXIT_RISK_DETECTED = 10
EXIT_GATE_VIOLATION = 12

COMMANDS = {
    "analyze",
    "capture",
    "replay",
    "serve",
    "purge",
    "start",
    "doctor",
    "scan",
    "protect",
    "demo",
    "challenge",
    "export",
    "lab",
    "inquire",
    "experiment",
    "eval-kit",
    "config",
    "share",
    "packs",
    "studio",
    "launch",
}



def _load_rules(path: Path | None) -> list[dict]:
    if path is None:
        return DEFAULT_RULES

    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        rules = raw.get("rules", [])
    else:
        rules = raw

    if not isinstance(rules, list):
        raise ValidationError("Rules file must be a list or {rules: [...]} object.")
    return [rule for rule in rules if isinstance(rule, dict)]



def _emit_json(payload: dict, output: str, pretty: bool) -> None:
    text = json.dumps(payload, indent=2 if pretty else None)
    if output == "-":
        print(text)
        return
    Path(output).write_text(text + "\n", encoding="utf-8")



def _build_markdown_report(report: dict) -> str:
    lines = [
        "# Honeypot Med Report",
        "",
        f"- Total events: {report.get('total_prompts', 0)}",
        f"- High risk events: {report.get('high_risk_count', 0)}",
        f"- Hypotheses: {report.get('hypotheses_count', 0)}",
        f"- Proven findings: {report.get('proven_findings_count', 0)}",
        f"- Suppressed findings: {report.get('suppressed_finding_count', 0)}",
        "",
        "| Prompt | Severity | Risk | Findings | Proven |",
        "|---|---|---:|---:|---:|",
    ]
    for event in report.get("events", []):
        prompt = str(event.get("prompt", "")).replace("|", "\\|")
        if len(prompt) > 80:
            prompt = prompt[:77] + "..."
        lines.append(
            "| {prompt} | {severity} | {risk} | {findings} | {proven} |".format(
                prompt=prompt,
                severity=event.get("severity", "low"),
                risk=event.get("risk_score", 0),
                findings=event.get("finding_count", 0),
                proven=event.get("proven_count", 0),
            )
        )
    lines.append("")
    return "\n".join(lines)



def _emit_markdown_report(report: dict, markdown_path: str | None) -> None:
    if not markdown_path:
        return
    markdown = _build_markdown_report(report)
    Path(markdown_path).write_text(markdown + "\n", encoding="utf-8")


def _add_source_flags(
    parser: argparse.ArgumentParser,
    *,
    default_input: str | None = None,
    input_help: str,
) -> None:
    parser.set_defaults(_default_input=default_input)
    parser.add_argument("--input", help=input_help)
    parser.add_argument("--pack", help="Run one of the bundled healthcare attack packs")
    parser.add_argument(
        "--prompt",
        help="Analyze a pasted prompt directly without creating a JSON file first",
    )


def _load_analysis_payload(args: argparse.Namespace) -> tuple[InputPayload, dict, str]:
    prompt = getattr(args, "prompt", None)
    explicit_input = getattr(args, "input", None)
    explicit_pack_id = getattr(args, "pack", None)
    default_pack_id = getattr(args, "_default_pack", None)
    default_input = getattr(args, "_default_input", None)

    provided = [bool(prompt), bool(explicit_input), bool(explicit_pack_id)]
    if sum(1 for item in provided if item) > 1:
        raise ValidationError("Use only one source: --input, --prompt, or --pack.")

    if prompt:
        payload_dict = {
            "events": [
                {
                    "prompt": str(prompt).strip(),
                    "tool_calls": [],
                    "model_output": "",
                    "response": "",
                }
            ]
        }
        return InputPayload.from_dict(payload_dict), payload_dict, "pasted prompt"

    pack_id = explicit_pack_id or (default_pack_id if not prompt and not explicit_input else None)
    if pack_id:
        payload_dict = load_attack_pack_payload(str(pack_id))
        return InputPayload.from_dict(payload_dict), payload_dict, f"pack:{pack_id}"

    input_path = explicit_input or default_input
    if input_path:
        raw_payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
        if not isinstance(raw_payload, dict):
            raise ValidationError("Input file must be a JSON object.")
        return InputPayload.from_dict(raw_payload), raw_payload, str(input_path)

    raise ValidationError("Provide one source: --input <file>, --prompt <text>, or --pack <id>.")


def _load_capture_events_from_args(args: argparse.Namespace) -> list[dict]:
    prompt = getattr(args, "prompt", None)
    explicit_input = getattr(args, "input", None)
    pack_id = getattr(args, "pack", None)

    provided = [bool(prompt), bool(explicit_input), bool(pack_id)]
    if sum(1 for item in provided if item) > 1:
        raise ValidationError("Use only one source: --input, --prompt, or --pack.")

    if prompt:
        return [{"prompt": str(prompt).strip()}]

    if pack_id:
        return _extract_capture_events(load_attack_pack_payload(str(pack_id)))

    if not explicit_input:
        raise ValidationError("Capture requires --input <file>, --prompt <text>, or --pack <id>.")

    raw = json.loads(Path(explicit_input).read_text(encoding="utf-8"))
    return _extract_capture_events(raw)


def _gate_violations(report: dict, args: argparse.Namespace) -> list[str]:
    violations = []
    critical = int(report["severity_counts"]["critical"])
    high = int(report["severity_counts"]["high"])
    unproven = int(report["unproven_count"])

    if critical > args.max_critical:
        violations.append(f"critical={critical} exceeds max_critical={args.max_critical}")
    if high > args.max_high:
        violations.append(f"high={high} exceeds max_high={args.max_high}")
    if unproven > args.max_unproven:
        violations.append(f"unproven={unproven} exceeds max_unproven={args.max_unproven}")
    return violations



def _check_policy(report: dict, args: argparse.Namespace) -> int:
    if args.gate:
        violations = _gate_violations(report, args)
        if violations:
            for item in violations:
                LOGGER.warning("Gate violation: %s", item)
            return EXIT_GATE_VIOLATION

    if args.strict and report["high_risk_count"] > 0:
        LOGGER.warning("High-risk findings detected in strict mode")
        return EXIT_RISK_DETECTED

    return EXIT_OK



def _add_runtime_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", help="Runtime config path (default ~/.honeypot-med/config.json)")
    parser.add_argument("--engine-mode", choices=["auto", "local", "hybrid", "remote"], default=None)
    parser.add_argument("--remote-url", help="Optional remote engine URL for hybrid/remote mode")
    parser.add_argument("--remote-auth-token", help="Optional bearer token for remote engine")
    parser.add_argument("--remote-timeout-sec", type=int, default=None)
    parser.add_argument("--remote-retries", type=int, default=None)
    parser.add_argument(
        "--allow-network",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Allow network for remote/hybrid engine mode",
    )



def _add_scoring_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--rules", help="Optional custom rules JSON")
    parser.add_argument("--baseline", help="Optional suppression baseline JSON")
    parser.add_argument("--min-high-risk", type=int, default=60, help="Risk threshold for high severity")
    parser.add_argument("--proof-required", action=argparse.BooleanOptionalAction, default=True)


def _apply_runtime_overrides(config: dict, args: argparse.Namespace, *, include_paths: bool = False) -> None:
    if getattr(args, "engine_mode", None) is not None:
        config["engine_mode"] = args.engine_mode
    if getattr(args, "remote_url", None) is not None:
        config["remote_engine_url"] = args.remote_url
    if getattr(args, "remote_auth_token", None) is not None:
        config["remote_auth_token"] = args.remote_auth_token
    if getattr(args, "remote_timeout_sec", None) is not None:
        config["remote_timeout_sec"] = int(args.remote_timeout_sec)
    if getattr(args, "remote_retries", None) is not None:
        config["remote_retries"] = int(args.remote_retries)
    if getattr(args, "allow_network", None) is not None:
        config["allow_network"] = bool(args.allow_network)

    if not include_paths:
        return

    if getattr(args, "asset_dir", None):
        config["asset_dir"] = str(Path(args.asset_dir).expanduser())
    if getattr(args, "store", None):
        config["store_path"] = str(Path(args.store).expanduser())
    if getattr(args, "audit_log_path", None):
        config["audit_log_path"] = str(Path(args.audit_log_path).expanduser())


def _add_analysis_flags(parser: argparse.ArgumentParser) -> None:
    _add_scoring_flags(parser)
    parser.add_argument("--markdown", help="Optional markdown report output path")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when high/critical findings exist")
    parser.add_argument("--gate", action="store_true", help="Apply security gate thresholds and fail on violations")
    parser.add_argument("--max-critical", type=int, default=0)
    parser.add_argument("--max-high", type=int, default=0)
    parser.add_argument("--max-unproven", type=int, default=999)



def _build_command_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Honeypot Med - intuitive prompt injection honeypot for local and internet-enabled workflows"
    )
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze payload from JSON file")
    _add_source_flags(
        analyze,
        input_help="JSON file with {events:[...]} or {prompts:[...]} payload",
    )
    analyze.add_argument("--output", default="-", help="Output JSON path or '-' for stdout")
    analyze.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    _add_analysis_flags(analyze)
    _add_runtime_flags(analyze)

    replay = subparsers.add_parser("replay", help="Replay events from JSONL store and analyze")
    replay.add_argument("--store", required=True, help="Path to JSONL store file")
    replay.add_argument("--output", default="-", help="Output JSON path or '-' for stdout")
    replay.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    _add_analysis_flags(replay)
    _add_runtime_flags(replay)

    capture = subparsers.add_parser("capture", help="Capture event payload into JSONL store")
    _add_source_flags(
        capture,
        input_help="JSON file containing event, events, or prompts",
    )
    capture.add_argument("--store", default="data/events.jsonl", help="JSONL event store path")
    capture.add_argument("--source", default="cli.capture", help="Default source for captured events")
    capture.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    serve = subparsers.add_parser("serve", help="Run decoy capture HTTP service")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8787)
    serve.add_argument("--store", default="data/events.jsonl", help="JSONL event store path")
    serve.add_argument("--api-key", help="API key for bearer auth on POST endpoints")
    serve.add_argument("--api-key-env", default="HONEYPOT_MED_API_KEY")
    serve.add_argument("--decoy-pack", help="Optional JSON decoy pack file")
    serve.add_argument("--max-body-bytes", type=int, default=1_000_000)
    serve.add_argument("--min-high-risk", type=int, default=60)
    serve.add_argument("--proof-required", action=argparse.BooleanOptionalAction, default=True)

    purge = subparsers.add_parser("purge", help="Purge old events from JSONL store")
    purge.add_argument("--store", required=True, help="JSONL event store path")
    purge.add_argument("--days", type=int, default=30, help="Retention window in days")
    purge.add_argument("--apply", action="store_true", help="Apply deletion (default is dry-run)")
    purge.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    start = subparsers.add_parser("start", help="First-run setup for non-developers")
    start.add_argument("--config", help="Runtime config path")
    start.add_argument("--engine-mode", choices=["auto", "local", "hybrid", "remote"], default=None)
    start.add_argument("--remote-url", help="Optional remote engine URL")
    start.add_argument("--remote-auth-token", help="Optional bearer token for remote engine")
    start.add_argument("--remote-timeout-sec", type=int, default=None)
    start.add_argument("--remote-retries", type=int, default=None)
    start.add_argument("--allow-network", action=argparse.BooleanOptionalAction, default=None)
    start.add_argument("--asset-dir", help="Asset cache directory")
    start.add_argument("--store", help="Default event store path")
    start.add_argument("--audit-log-path", help="Audit log path")
    start.add_argument("--download-assets", action="store_true", help="Attempt online asset bootstrap")
    start.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    doctor = subparsers.add_parser("doctor", help="Check local setup health")
    doctor.add_argument("--config", help="Runtime config path")
    doctor.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    scan = subparsers.add_parser("scan", help="Beginner scan command with plain-English summary")
    _add_source_flags(
        scan,
        default_input="examples/sample.json",
        input_help="JSON file with {events:[...]} or {prompts:[...]} payload",
    )
    scan.add_argument("--json", action="store_true", help="Emit full JSON report")
    scan.add_argument("--output", default="-", help="JSON output path when --json is set")
    scan.add_argument("--pretty", action="store_true")
    scan.add_argument("--bundle-dir", help="Also write HTML, SVG, JSON, Markdown, SARIF, and OTEL artifacts")
    scan.add_argument("--title", help="Optional bundle title when --bundle-dir is set")
    _add_analysis_flags(scan)
    _add_runtime_flags(scan)

    protect = subparsers.add_parser("protect", help="Run policy gate checks with safe defaults")
    _add_source_flags(
        protect,
        default_input="examples/clean.json",
        input_help="JSON file with {events:[...]} or {prompts:[...]} payload",
    )
    protect.add_argument("--max-critical", type=int, default=0)
    protect.add_argument("--max-high", type=int, default=0)
    protect.add_argument("--max-unproven", type=int, default=0)
    protect.add_argument("--baseline", help="Optional baseline JSON")
    protect.add_argument("--json", action="store_true")
    protect.add_argument("--pretty", action="store_true")
    _add_runtime_flags(protect)

    demo = subparsers.add_parser("demo", help="Run one-command showcase flow")
    demo.add_argument("--reports-dir", default="reports")
    demo.add_argument("--pretty", action="store_true")
    _add_runtime_flags(demo)

    share = subparsers.add_parser("share", help="Generate a shareable HTML report bundle")
    _add_source_flags(
        share,
        default_input="examples/sample.json",
        input_help="JSON file with {events:[...]} or {prompts:[...]} payload",
    )
    share.add_argument("--outdir", default="reports/share")
    share.add_argument("--title", help="Optional share-page title")
    share.add_argument("--json", action="store_true", help="Emit bundle metadata as JSON")
    _add_scoring_flags(share)
    _add_runtime_flags(share)

    challenge = subparsers.add_parser("challenge", help="Run the public healthcare AI trap challenge")
    _add_source_flags(
        challenge,
        input_help="Optional JSON payload; defaults to the bundled healthcare challenge pack",
    )
    challenge.set_defaults(_default_pack=DEFAULT_CHALLENGE_PACK)
    challenge.add_argument("--outdir", default="reports/challenge")
    challenge.add_argument("--title", default="Honeypot Med Healthcare AI Challenge")
    challenge.add_argument("--report-url", default="index.html")
    challenge.add_argument("--fail-under", type=int, default=0, help="Fail if survival score is below this percentage")
    challenge.add_argument("--json", action="store_true", help="Emit challenge metadata as JSON")
    _add_scoring_flags(challenge)
    _add_runtime_flags(challenge)

    export = subparsers.add_parser("export", help="Export a report in portable integration formats")
    _add_source_flags(
        export,
        default_input="examples/sample.json",
        input_help="JSON file with {events:[...]} or {prompts:[...]} payload",
    )
    export.add_argument(
        "--format",
        choices=["all", "html", "json", "markdown", "sarif", "otel", "badge", "eval-kit"],
        default="all",
    )
    export.add_argument("--outdir", default="reports/export")
    export.add_argument("--title", default="Honeypot Med Export")
    export.add_argument("--json", action="store_true", help="Emit artifact metadata as JSON")
    _add_scoring_flags(export)
    _add_runtime_flags(export)

    lab = subparsers.add_parser("lab", help="Generate weird offline Trap Lab artifacts")
    _add_source_flags(
        lab,
        input_help="Optional JSON payload; defaults to the bundled healthcare challenge pack",
    )
    lab.set_defaults(_default_pack=DEFAULT_CHALLENGE_PACK)
    lab.add_argument("--outdir", default="reports/lab")
    lab.add_argument("--title", default="Honeypot Med Trap Lab")
    lab.add_argument("--json", action="store_true", help="Emit lab artifact metadata as JSON")
    _add_scoring_flags(lab)
    _add_runtime_flags(lab)

    inquire = subparsers.add_parser("inquire", help="Generate research questions and unknown ledgers")
    _add_source_flags(
        inquire,
        input_help="Optional JSON payload; defaults to the bundled healthcare challenge pack",
    )
    inquire.set_defaults(_default_pack=DEFAULT_CHALLENGE_PACK)
    inquire.add_argument("--outdir", default="reports/inquiry")
    inquire.add_argument("--title", default="Honeypot Med Inquiry")
    inquire.add_argument("--json", action="store_true", help="Emit inquiry artifact metadata as JSON")
    _add_scoring_flags(inquire)
    _add_runtime_flags(inquire)

    experiment = subparsers.add_parser("experiment", help="Generate counterfactual prompts and ablation plans")
    _add_source_flags(
        experiment,
        input_help="Optional JSON payload; defaults to the bundled healthcare challenge pack",
    )
    experiment.set_defaults(_default_pack=DEFAULT_CHALLENGE_PACK)
    experiment.add_argument("--outdir", default="reports/experiments")
    experiment.add_argument("--title", default="Honeypot Med Experiment")
    experiment.add_argument("--json", action="store_true", help="Emit experiment artifact metadata as JSON")
    _add_scoring_flags(experiment)
    _add_runtime_flags(experiment)

    eval_kit = subparsers.add_parser("eval-kit", help="Generate offline adapters for promptfoo, Inspect AI, and OpenAI Evals")
    _add_source_flags(
        eval_kit,
        input_help="Optional JSON payload; defaults to the bundled healthcare challenge pack",
    )
    eval_kit.set_defaults(_default_pack=DEFAULT_CHALLENGE_PACK)
    eval_kit.add_argument("--outdir", default="reports/eval-kit")
    eval_kit.add_argument("--title", default="Honeypot Med Eval Kit")
    eval_kit.add_argument("--json", action="store_true", help="Emit eval-kit artifact metadata as JSON")
    _add_scoring_flags(eval_kit)
    _add_runtime_flags(eval_kit)

    packs = subparsers.add_parser("packs", help="List or inspect bundled healthcare attack packs")
    packs.add_argument("--pack", help="Specific pack id to inspect")
    packs.add_argument("--json", action="store_true")

    studio = subparsers.add_parser("studio", help="Launch the hosted local browser experience")
    studio.add_argument("--host", default="127.0.0.1")
    studio.add_argument("--port", type=int, default=8899)
    studio.add_argument("--open-browser", action=argparse.BooleanOptionalAction, default=True)
    _add_runtime_flags(studio)

    launch = subparsers.add_parser("launch", help="Initialize local runtime and open the browser studio")
    launch.add_argument("--host", default="127.0.0.1")
    launch.add_argument("--port", type=int, default=8899)
    launch.add_argument("--open-browser", action=argparse.BooleanOptionalAction, default=True)
    launch.add_argument("--asset-dir", help="Asset cache directory")
    launch.add_argument("--store", help="Default event store path")
    launch.add_argument("--audit-log-path", help="Audit log path")
    launch.add_argument("--download-assets", action="store_true", help="Attempt online asset bootstrap")
    _add_runtime_flags(launch)

    config_cmd = subparsers.add_parser("config", help="Show or update runtime config")
    config_sub = config_cmd.add_subparsers(dest="config_action", required=True)

    config_show = config_sub.add_parser("show", help="Show effective runtime config")
    config_show.add_argument("--config", help="Runtime config path")
    config_show.add_argument("--json", action="store_true")

    config_set = config_sub.add_parser("set", help="Update runtime config values")
    config_set.add_argument("--config", help="Runtime config path")
    config_set.add_argument("--engine-mode", choices=["auto", "local", "hybrid", "remote"], default=None)
    config_set.add_argument("--remote-url", default=None)
    config_set.add_argument("--remote-auth-token", default=None)
    config_set.add_argument("--remote-timeout-sec", type=int, default=None)
    config_set.add_argument("--remote-retries", type=int, default=None)
    config_set.add_argument("--allow-network", action=argparse.BooleanOptionalAction, default=None)
    config_set.add_argument("--asset-dir", default=None)
    config_set.add_argument("--store", default=None)
    config_set.add_argument("--audit-log-path", default=None)
    config_set.add_argument("--json", action="store_true")

    return parser



def _build_legacy_analyze_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prompt-injection honeypot and validation pipeline")
    parser.add_argument("--input", required=True, help="JSON file with {events:[...]} or {prompts:[...]} payload")
    parser.add_argument("--output", default="-", help="Output JSON path or '-' for stdout")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    _add_analysis_flags(parser)
    _add_runtime_flags(parser)
    return parser



def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )



def _resolve_runtime_settings(
    args: argparse.Namespace,
) -> tuple[dict, Path, str, str | None, str | None, bool, int, int]:
    config, config_path = load_runtime_config(getattr(args, "config", None))

    engine_mode = args.engine_mode if args.engine_mode is not None else str(config.get("engine_mode", "auto"))
    remote_url = args.remote_url if args.remote_url is not None else config.get("remote_engine_url")
    remote_auth_token = (
        args.remote_auth_token
        if getattr(args, "remote_auth_token", None) is not None
        else config.get("remote_auth_token")
    )

    allow_network = args.allow_network
    if allow_network is None:
        allow_network = bool(config.get("allow_network", True))

    timeout_sec = (
        int(args.remote_timeout_sec)
        if getattr(args, "remote_timeout_sec", None) is not None
        else int(config.get("remote_timeout_sec", 8))
    )
    retries = (
        int(args.remote_retries)
        if getattr(args, "remote_retries", None) is not None
        else int(config.get("remote_retries", 1))
    )

    return (
        config,
        config_path,
        engine_mode,
        (str(remote_url) if remote_url else None),
        (str(remote_auth_token) if remote_auth_token else None),
        bool(allow_network),
        timeout_sec,
        retries,
    )



def _build_analysis_report(
    payload: InputPayload,
    payload_dict: dict,
    args: argparse.Namespace,
) -> dict:
    rules = _load_rules(Path(args.rules)) if args.rules else DEFAULT_RULES
    report = analyze_prompts(
        payload,
        rules=rules,
        min_high_risk=args.min_high_risk,
        proof_required=args.proof_required,
    )

    if args.baseline:
        baseline_raw = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        suppressions = load_suppressions(baseline_raw)
        report = apply_suppressions(report, suppressions)

    (
        _,
        _,
        engine_mode,
        remote_url,
        remote_auth_token,
        allow_network,
        timeout_sec,
        retries,
    ) = _resolve_runtime_settings(args)
    report = enrich_report_with_engine(
        report,
        payload_dict,
        mode=engine_mode,
        remote_url=remote_url,
        remote_auth_token=remote_auth_token,
        allow_network=allow_network,
        timeout_sec=timeout_sec,
        retries=retries,
    )
    return report



def _run_analyze(args: argparse.Namespace) -> int:
    payload, payload_dict, _ = _load_analysis_payload(args)
    report = _build_analysis_report(payload, payload_dict, args)
    _emit_json(report, args.output, args.pretty)
    _emit_markdown_report(report, args.markdown)
    return _check_policy(report, args)



def _run_replay(args: argparse.Namespace) -> int:
    events = JSONLStore(args.store).read_all()
    payload_dict = events_to_payload(events)
    payload = InputPayload.from_dict(payload_dict)

    report = _build_analysis_report(payload, payload_dict, args)
    report["replay_source"] = str(args.store)
    _emit_json(report, args.output, args.pretty)
    _emit_markdown_report(report, args.markdown)
    return _check_policy(report, args)



def _extract_capture_events(raw: dict) -> list[dict]:
    if not isinstance(raw, dict):
        raise ValidationError("Capture input must be a JSON object")

    if "event" in raw:
        event = raw["event"]
        if not isinstance(event, dict):
            raise ValidationError("Field 'event' must be an object")
        return [event]

    if "events" in raw or "prompts" in raw:
        payload = InputPayload.from_dict(raw)
        events: list[dict] = []
        for entry in payload.events:
            events.append(
                {
                    "prompt": entry.prompt,
                    "tool_calls": [
                        {"name": tool.name, "args": tool.args} for tool in entry.tool_calls
                    ],
                    "model_output": entry.model_output,
                    "response": entry.response,
                }
            )
        return events

    if "prompt" in raw:
        return [raw]

    raise ValidationError("Capture input must contain 'event', 'events', 'prompts', or 'prompt'")



def _run_capture(args: argparse.Namespace) -> int:
    capture_events = _load_capture_events_from_args(args)
    normalized_events = []
    redaction_hits = 0
    for event in capture_events:
        redacted_event, hits = redact_event(event)
        redaction_hits += hits
        normalized_events.append(normalize_event(redacted_event, default_source=args.source))
    store = JSONLStore(args.store)
    store.append_many(normalized_events)

    summary = {
        "status": "captured",
        "captured_count": len(normalized_events),
        "redaction_hits": redaction_hits,
        "store": str(args.store),
        "event_ids": [event["event_id"] for event in normalized_events],
    }
    _emit_json(summary, "-", args.pretty)
    return EXIT_OK



def _run_serve(args: argparse.Namespace) -> int:
    api_key = args.api_key or os.getenv(args.api_key_env)
    decoy_routes = tuple(load_decoy_pack(args.decoy_pack)) if args.decoy_pack else ()
    run_server(
        args.host,
        args.port,
        store_path=Path(args.store),
        min_high_risk=args.min_high_risk,
        proof_required=args.proof_required,
        api_key=api_key,
        decoy_routes=decoy_routes,
        max_body_bytes=args.max_body_bytes,
    )
    return EXIT_OK



def _run_purge(args: argparse.Namespace) -> int:
    store = JSONLStore(args.store)
    purged_rows, kept_rows = store.split_by_age(args.days)

    if args.apply and purged_rows:
        store.overwrite(kept_rows)

    summary = {
        "status": "purge_applied" if args.apply else "dry_run",
        "store": str(args.store),
        "days": args.days,
        "purged_count": len(purged_rows),
        "kept_count": len(kept_rows),
    }
    _emit_json(summary, "-", args.pretty)
    return EXIT_OK



def _run_start(args: argparse.Namespace) -> int:
    config, config_path = load_runtime_config(args.config)
    _apply_runtime_overrides(config, args, include_paths=True)

    config["last_bootstrap"] = datetime.now(timezone.utc).isoformat()

    runtime_dirs = ensure_runtime_dirs(config)

    bootstrap = {
        "network_checked": False,
        "network_available": False,
        "asset_marker_created": False,
    }

    if args.download_assets:
        bootstrap["network_checked"] = True
        bootstrap["network_available"] = check_network()
        if bootstrap["network_available"]:
            marker = Path(runtime_dirs["asset_dir"]) / "READY.txt"
            marker.write_text(
                "honeypot-med runtime initialized for local/hybrid/remote use\n",
                encoding="utf-8",
            )
            bootstrap["asset_marker_created"] = True

    save_runtime_config(config, args.config)

    payload = {
        "status": "initialized",
        "config_path": str(config_path),
        "engine_mode": config["engine_mode"],
        "remote_engine_url": config.get("remote_engine_url"),
        "remote_timeout_sec": int(config.get("remote_timeout_sec", 8)),
        "remote_retries": int(config.get("remote_retries", 1)),
        "allow_network": bool(config.get("allow_network", True)),
        "asset_dir": runtime_dirs["asset_dir"],
        "store_path": runtime_dirs["store_path"],
        "audit_log_path": runtime_dirs["audit_log_path"],
        "bootstrap": bootstrap,
    }

    if args.json:
        _emit_json(payload, "-", True)
        return EXIT_OK

    print("Honeypot Med is ready.")
    print(f"- Runtime config: {payload['config_path']}")
    print(f"- Engine mode: {payload['engine_mode']}")
    print(f"- Asset cache: {payload['asset_dir']}")
    print(f"- Event store: {payload['store_path']}")
    print(f"- Audit log: {payload['audit_log_path']}")
    if args.download_assets:
        if bootstrap["network_available"]:
            print("- Online bootstrap: complete")
        else:
            print("- Online bootstrap: skipped (offline)")
    print("Next: run `honeypot-med studio` or `honeypot-med scan`.")
    return EXIT_OK


def _run_launch(args: argparse.Namespace) -> int:
    config, config_path = load_runtime_config(args.config)
    _apply_runtime_overrides(config, args, include_paths=True)
    config["last_bootstrap"] = datetime.now(timezone.utc).isoformat()
    runtime_dirs = ensure_runtime_dirs(config)

    if args.download_assets and check_network():
        marker = Path(runtime_dirs["asset_dir"]) / "READY.txt"
        marker.write_text(
            "honeypot-med runtime initialized for local/hybrid/remote use\n",
            encoding="utf-8",
        )

    save_runtime_config(config, args.config)

    print("Launching Honeypot Med Studio.")
    print("- Free local mode: enabled")
    print("- API keys: not required")
    print(f"- Config: {config_path}")
    print(f"- Browser URL: http://{args.host}:{args.port}")

    run_studio_server(
        args.host,
        args.port,
        config=config,
        open_browser=bool(args.open_browser),
    )
    return EXIT_OK



def _run_doctor(args: argparse.Namespace) -> int:
    config, config_path = load_runtime_config(args.config)
    dirs = ensure_runtime_dirs(config)
    network_ok = check_network()

    payload = {
        "status": "ok",
        "config_path": str(config_path),
        "config_exists": config_path.exists(),
        "engine_mode": config.get("engine_mode", "auto"),
        "remote_engine_url": config.get("remote_engine_url"),
        "remote_auth_configured": bool(config.get("remote_auth_token")),
        "remote_timeout_sec": int(config.get("remote_timeout_sec", 8)),
        "remote_retries": int(config.get("remote_retries", 1)),
        "allow_network": bool(config.get("allow_network", True)),
        "asset_dir": dirs["asset_dir"],
        "asset_dir_exists": Path(dirs["asset_dir"]).exists(),
        "store_path": dirs["store_path"],
        "store_parent_exists": Path(dirs["store_path"]).parent.exists(),
        "audit_log_path": dirs["audit_log_path"],
        "audit_log_parent_exists": Path(dirs["audit_log_path"]).parent.exists(),
        "network_reachable": network_ok,
    }

    if args.json:
        _emit_json(payload, "-", True)
        return EXIT_OK

    print("Honeypot Med doctor")
    print(f"- Config: {payload['config_path']}")
    print(f"- Engine mode: {payload['engine_mode']}")
    print(f"- Network reachable: {'yes' if network_ok else 'no'}")
    print(f"- Asset dir ready: {'yes' if payload['asset_dir_exists'] else 'no'}")
    print(f"- Store parent ready: {'yes' if payload['store_parent_exists'] else 'no'}")
    print(f"- Audit path ready: {'yes' if payload['audit_log_parent_exists'] else 'no'}")
    return EXIT_OK



def _scan_summary(report: dict) -> str:
    sev = report.get("severity_counts", {})
    top = "critical" if sev.get("critical", 0) else "high" if sev.get("high", 0) else "medium" if sev.get("medium", 0) else "low"

    lines = [
        "Scan complete.",
        f"- Risk level: {top}",
        f"- Events analyzed: {report.get('total_prompts', 0)}",
        f"- High-risk events: {report.get('high_risk_count', 0)}",
        f"- Proven findings: {report.get('proven_findings_count', 0)}",
    ]

    engine = report.get("engine", {})
    if isinstance(engine, dict):
        lines.append(f"- Engine: {engine.get('provider', 'deterministic-local')}")

    if report.get("high_risk_count", 0) > 0:
        lines.append("- Next: run `honeypot-med share --input <file>` or `honeypot-med protect --input <file>`.")
    else:
        lines.append("- Next: run `honeypot-med share` to generate a buyer-friendly proof page.")

    return "\n".join(lines)



def _run_scan(args: argparse.Namespace) -> int:
    payload, payload_dict, source_label = _load_analysis_payload(args)
    report = _build_analysis_report(payload, payload_dict, args)

    if args.json:
        _emit_json(report, args.output, args.pretty)
    else:
        print(_scan_summary(report))
        if args.output != "-":
            _emit_json(report, args.output, True)

    _emit_markdown_report(report, args.markdown)
    if getattr(args, "bundle_dir", None):
        bundle = write_share_bundle(
            report,
            args.bundle_dir,
            source_label=source_label,
            title=getattr(args, "title", None),
        )
        if not args.json:
            print(f"- Share bundle: {bundle['html_path']}")
            print(f"- SARIF export: {bundle['sarif_path']}")
            print(f"- OTEL logs: {bundle['otel_logs_path']}")
    return EXIT_OK



def _run_protect(args: argparse.Namespace) -> int:
    payload, payload_dict, _ = _load_analysis_payload(args)

    shadow_args = argparse.Namespace(
        rules=None,
        baseline=args.baseline,
        min_high_risk=60,
        proof_required=True,
        engine_mode=args.engine_mode,
        remote_url=args.remote_url,
        remote_auth_token=getattr(args, "remote_auth_token", None),
        remote_timeout_sec=getattr(args, "remote_timeout_sec", None),
        remote_retries=getattr(args, "remote_retries", None),
        allow_network=args.allow_network,
        config=args.config,
    )
    report = _build_analysis_report(payload, payload_dict, shadow_args)

    policy_args = argparse.Namespace(
        gate=True,
        strict=False,
        max_critical=args.max_critical,
        max_high=args.max_high,
        max_unproven=args.max_unproven,
    )
    status = _check_policy(report, policy_args)

    if args.json:
        _emit_json(
            {
                "status": "passed" if status == EXIT_OK else "blocked",
                "policy": {
                    "max_critical": args.max_critical,
                    "max_high": args.max_high,
                    "max_unproven": args.max_unproven,
                },
                "report": report,
            },
            "-",
            args.pretty,
        )
        return status

    if status == EXIT_OK:
        print("Protection check passed.")
        print("- No gate violations detected.")
        return EXIT_OK

    print("Protection check blocked release.")
    for item in _gate_violations(report, policy_args):
        print(f"- {item}")
    print("- Next: inspect report with `honeypot-med scan --json --input <file>`.")
    return status


def _run_share(args: argparse.Namespace) -> int:
    payload, payload_dict, source_label = _load_analysis_payload(args)
    report = _build_analysis_report(payload, payload_dict, args)
    bundle = write_share_bundle(report, args.outdir, source_label=source_label, title=args.title)

    if args.json:
        _emit_json({"bundle": bundle, "report": report}, "-", True)
        return EXIT_OK

    print("Share bundle ready.")
    print(f"- Verdict page: {bundle['html_path']}")
    print(f"- JSON report: {bundle['json_path']}")
    print(f"- Markdown report: {bundle['markdown_path']}")
    print(f"- Social card: {bundle['social_card_path']}")
    print(f"- PDF brief: {bundle['pdf_path']}")
    print(f"- README badge: {bundle['badge_path']}")
    print(f"- SARIF export: {bundle['sarif_path']}")
    print(f"- OTEL logs: {bundle['otel_logs_path']}")
    return EXIT_OK


def _run_challenge(args: argparse.Namespace) -> int:
    payload, payload_dict, source_label = _load_analysis_payload(args)
    report = _build_analysis_report(payload, payload_dict, args)
    bundle = write_challenge_bundle(
        report,
        args.outdir,
        source_label=source_label,
        title=args.title,
        report_url=args.report_url,
    )
    challenge = bundle["challenge"]
    status = EXIT_OK
    if int(challenge["score_percent"]) < int(args.fail_under):
        status = EXIT_GATE_VIOLATION

    if args.json:
        _emit_json({"bundle": bundle, "challenge": challenge, "report": report}, "-", True)
        return status

    print("Challenge complete.")
    print(f"- Score: {challenge['score_label']}")
    print(f"- Verdict: {challenge['verdict']}")
    print(f"- Report: {bundle['html_path']}")
    print(f"- Badge: {bundle['extra_artifacts']['badge']}")
    print(f"- SARIF: {bundle['extra_artifacts']['sarif']}")
    print(f"- OTEL logs: {bundle['extra_artifacts']['otel_logs']}")
    if status != EXIT_OK:
        print(f"- Gate: score {challenge['score_percent']} is below fail-under {args.fail_under}")
    return status


def _run_export(args: argparse.Namespace) -> int:
    payload, payload_dict, source_label = _load_analysis_payload(args)
    report = _build_analysis_report(payload, payload_dict, args)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, str] = {}
    selected = args.format
    if selected in {"all", "html"}:
        bundle = write_share_bundle(report, str(outdir), source_label=source_label, title=args.title)
        artifacts.update(
            {
                "html": bundle["html_path"],
                "json": bundle["json_path"],
                "markdown": bundle["markdown_path"],
                "social_card": bundle["social_card_path"],
                "badge": bundle["badge_path"],
                "sarif": bundle["sarif_path"],
                "otel_logs": bundle["otel_logs_path"],
            }
        )
    else:
        if selected == "json":
            path = outdir / "report.json"
            path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            artifacts["json"] = str(path)
        elif selected == "markdown":
            path = outdir / "report.md"
            path.write_text(_build_markdown_report(report) + "\n", encoding="utf-8")
            artifacts["markdown"] = str(path)
        elif selected == "sarif":
            path = outdir / "honeypot-med.sarif"
            path.write_text(
                json.dumps(report_to_sarif(report, source_label=source_label), indent=2) + "\n",
                encoding="utf-8",
            )
            artifacts["sarif"] = str(path)
        elif selected == "otel":
            path = outdir / "otel-logs.json"
            path.write_text(
                json.dumps(report_to_otel_logs(report, source_label=source_label), indent=2) + "\n",
                encoding="utf-8",
            )
            artifacts["otel_logs"] = str(path)
        elif selected == "badge":
            badge_path = outdir / "badge.svg"
            markdown_path = outdir / "README-badge.md"
            badge_path.write_text(build_report_badge_svg(report), encoding="utf-8")
            markdown_path.write_text(
                build_badge_markdown(report_url="index.html", badge_path=badge_path.name),
                encoding="utf-8",
            )
            artifacts["badge"] = str(badge_path)
            artifacts["badge_markdown"] = str(markdown_path)
        elif selected == "eval-kit":
            artifacts.update(
                write_eval_adapter_artifacts(
                    report,
                    str(outdir),
                    source_label=source_label,
                    title=args.title,
                )
            )

    payload_out = {"status": "created", "format": selected, "outdir": str(outdir), "artifacts": artifacts}
    if args.json:
        _emit_json(payload_out, "-", True)
        return EXIT_OK

    print("Export complete.")
    for name, path in artifacts.items():
        print(f"- {name}: {path}")
    return EXIT_OK


def _run_lab(args: argparse.Namespace) -> int:
    payload, payload_dict, source_label = _load_analysis_payload(args)
    report = _build_analysis_report(payload, payload_dict, args)
    artifacts = write_lab_artifacts(report, args.outdir, source_label=source_label, title=args.title)
    payload_out = {"status": "created", "outdir": args.outdir, "artifacts": artifacts}
    if args.json:
        _emit_json(payload_out, "-", True)
        return EXIT_OK

    print("Trap Lab artifacts ready.")
    print(f"- Specimen codex: {artifacts['specimen_codex']}")
    print(f"- Field guide: {artifacts['field_guide']}")
    print(f"- Trap ledger CSV: {artifacts['trap_ledger_csv']}")
    print(f"- Offline proof: {artifacts['offline_proof']}")
    return EXIT_OK


def _run_inquire(args: argparse.Namespace) -> int:
    payload, payload_dict, source_label = _load_analysis_payload(args)
    report = _build_analysis_report(payload, payload_dict, args)
    artifacts = write_inquiry_artifacts(report, args.outdir, source_label=source_label, title=args.title)
    payload_out = {"status": "created", "outdir": args.outdir, "artifacts": artifacts}
    if args.json:
        _emit_json(payload_out, "-", True)
        return EXIT_OK

    print("Inquiry artifacts ready.")
    print(f"- Research questions: {artifacts['research_questions']}")
    print(f"- Inquiry notebook: {artifacts['inquiry_notebook']}")
    print(f"- Unknown ledger: {artifacts['unknown_ledger']}")
    print(f"- Experiment plan: {artifacts['experiment_plan']}")
    return EXIT_OK


def _run_experiment(args: argparse.Namespace) -> int:
    payload, payload_dict, source_label = _load_analysis_payload(args)
    report = _build_analysis_report(payload, payload_dict, args)
    artifacts = write_experiment_artifacts(report, args.outdir, title=args.title)
    payload_out = {"status": "created", "outdir": args.outdir, "source_label": source_label, "artifacts": artifacts}
    if args.json:
        _emit_json(payload_out, "-", True)
        return EXIT_OK

    print("Experiment artifacts ready.")
    print(f"- Experiment plan: {artifacts['experiment_plan']}")
    print(f"- Counterfactual prompts: {artifacts['counterfactual_prompts']}")
    print(f"- Ablation ladder: {artifacts['ablation_ladder']}")
    print(f"- Question atlas: {artifacts['question_atlas']}")
    return EXIT_OK


def _run_eval_kit(args: argparse.Namespace) -> int:
    payload, payload_dict, source_label = _load_analysis_payload(args)
    report = _build_analysis_report(payload, payload_dict, args)
    artifacts = write_eval_adapter_artifacts(
        report,
        args.outdir,
        source_label=source_label,
        title=args.title,
    )
    payload_out = {"status": "created", "outdir": args.outdir, "source_label": source_label, "artifacts": artifacts}
    if args.json:
        _emit_json(payload_out, "-", True)
        return EXIT_OK

    print("Eval kit ready.")
    print(f"- promptfoo config: {artifacts['promptfoo_config']}")
    print(f"- Inspect dataset: {artifacts['inspect_dataset']}")
    print(f"- OpenAI Evals samples: {artifacts['openai_evals_samples']}")
    print(f"- Canonical samples: {artifacts['eval_samples']}")
    return EXIT_OK


def _run_packs(args: argparse.Namespace) -> int:
    if args.pack:
        payload = describe_attack_pack(args.pack)
        if args.json:
            _emit_json(payload, "-", True)
            return EXIT_OK

        print(payload["title"])
        print(f"- ID: {payload['id']}")
        print(f"- Domain: {payload['domain']}")
        print(f"- Events: {payload['event_count']}")
        print(f"- Description: {payload['description']}")
        return EXIT_OK

    packs = list_attack_packs()
    if args.json:
        _emit_json(
            {
                "packs": [
                    {
                        "id": pack.pack_id,
                        "title": pack.title,
                        "description": pack.description,
                        "domain": pack.domain,
                    }
                    for pack in packs
                ]
            },
            "-",
            True,
        )
        return EXIT_OK

    print("Bundled attack packs")
    for pack in packs:
        print(f"- {pack.pack_id}: {pack.title} ({pack.domain})")
    return EXIT_OK


def _run_studio(args: argparse.Namespace) -> int:
    config, _ = load_runtime_config(getattr(args, "config", None))
    _apply_runtime_overrides(config, args)
    ensure_runtime_dirs(config)
    run_studio_server(
        args.host,
        args.port,
        config=config,
        open_browser=bool(args.open_browser),
    )
    return EXIT_OK


def _run_demo(args: argparse.Namespace) -> int:
    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    scan_args = argparse.Namespace(
        input="examples/sample.json",
        pack=None,
        prompt=None,
        _default_input=None,
        json=True,
        output=str(reports_dir / "sample-report.json"),
        pretty=True,
        markdown=str(reports_dir / "sample-report.md"),
        rules=None,
        baseline=None,
        min_high_risk=60,
        strict=False,
        proof_required=True,
        gate=False,
        max_critical=0,
        max_high=0,
        max_unproven=999,
        engine_mode=args.engine_mode,
        remote_url=args.remote_url,
        remote_auth_token=args.remote_auth_token,
        remote_timeout_sec=args.remote_timeout_sec,
        remote_retries=args.remote_retries,
        allow_network=args.allow_network,
        config=args.config,
    )
    _run_scan(scan_args)

    replay_args = argparse.Namespace(
        store="examples/replay-fixture.jsonl",
        output=str(reports_dir / "replay-report.json"),
        pretty=True,
        markdown=str(reports_dir / "replay-report.md"),
        rules=None,
        baseline=None,
        min_high_risk=60,
        strict=False,
        proof_required=True,
        gate=False,
        max_critical=0,
        max_high=0,
        max_unproven=999,
        engine_mode=args.engine_mode,
        remote_url=args.remote_url,
        remote_auth_token=args.remote_auth_token,
        remote_timeout_sec=args.remote_timeout_sec,
        remote_retries=args.remote_retries,
        allow_network=args.allow_network,
        config=args.config,
    )
    _run_replay(replay_args)

    protect_args = argparse.Namespace(
        input="examples/clean.json",
        pack=None,
        prompt=None,
        _default_input=None,
        max_critical=0,
        max_high=0,
        max_unproven=0,
        baseline=None,
        json=False,
        pretty=args.pretty,
        engine_mode=args.engine_mode,
        remote_url=args.remote_url,
        remote_auth_token=args.remote_auth_token,
        remote_timeout_sec=args.remote_timeout_sec,
        remote_retries=args.remote_retries,
        allow_network=args.allow_network,
        config=args.config,
    )
    status = _run_protect(protect_args)

    share_args = argparse.Namespace(
        input="examples/sample.json",
        pack=None,
        prompt=None,
        _default_input=None,
        outdir=str(reports_dir / "share"),
        title="Honeypot Med Demo Snapshot",
        json=False,
        rules=None,
        baseline=None,
        min_high_risk=60,
        proof_required=True,
        engine_mode=args.engine_mode,
        remote_url=args.remote_url,
        remote_auth_token=args.remote_auth_token,
        remote_timeout_sec=args.remote_timeout_sec,
        remote_retries=args.remote_retries,
        allow_network=args.allow_network,
        config=args.config,
    )
    _run_share(share_args)

    print("Demo complete.")
    print(f"- {reports_dir / 'sample-report.json'}")
    print(f"- {reports_dir / 'sample-report.md'}")
    print(f"- {reports_dir / 'replay-report.json'}")
    print(f"- {reports_dir / 'replay-report.md'}")
    print(f"- {reports_dir / 'share' / 'index.html'}")
    print(f"- {reports_dir / 'share' / 'social-card.svg'}")
    print(f"- {reports_dir / 'share' / 'summary.pdf'}")

    return status


def _run_config(args: argparse.Namespace) -> int:
    config, config_path = load_runtime_config(getattr(args, "config", None))

    if args.config_action == "show":
        payload = {"config_path": str(config_path), "config": config}
        if args.json:
            _emit_json(payload, "-", True)
        else:
            print(f"Config path: {config_path}")
            print(json.dumps(config, indent=2))
        return EXIT_OK

    if args.config_action == "set":
        if args.engine_mode is not None:
            config["engine_mode"] = args.engine_mode
        if args.remote_url is not None:
            config["remote_engine_url"] = args.remote_url or None
        if args.remote_auth_token is not None:
            config["remote_auth_token"] = args.remote_auth_token or None
        if args.remote_timeout_sec is not None:
            config["remote_timeout_sec"] = int(args.remote_timeout_sec)
        if args.remote_retries is not None:
            config["remote_retries"] = int(args.remote_retries)
        if args.allow_network is not None:
            config["allow_network"] = bool(args.allow_network)
        if args.asset_dir is not None:
            config["asset_dir"] = str(Path(args.asset_dir).expanduser())
        if args.store is not None:
            config["store_path"] = str(Path(args.store).expanduser())
        if args.audit_log_path is not None:
            config["audit_log_path"] = str(Path(args.audit_log_path).expanduser())

        save_runtime_config(config, getattr(args, "config", None))
        ensure_runtime_dirs(config)
        payload = {"status": "updated", "config_path": str(config_path), "config": config}
        if args.json:
            _emit_json(payload, "-", True)
        else:
            print("Config updated.")
            print(f"- Path: {config_path}")
        return EXIT_OK

    raise ValidationError(f"Unsupported config action: {args.config_action}")


def _write_command_audit(command: str, args: argparse.Namespace, exit_code: int) -> None:
    config, _ = load_runtime_config(getattr(args, "config", None))
    ensure_runtime_dirs(config)
    event = {"command": command, "exit_code": int(exit_code)}

    for key in ("engine_mode", "remote_url", "allow_network"):
        if hasattr(args, key):
            value = getattr(args, key)
            if value is not None:
                event[key] = value

    append_audit_event(config["audit_log_path"], event)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    try:
        if not argv:
            argv = ["launch"]

        if argv and argv[0] in {"-h", "--help"}:
            parser = _build_command_parser()
            parser.print_help()
            return EXIT_OK

        if argv and (argv[0] in COMMANDS or not argv[0].startswith("-")):
            parser = _build_command_parser()
            args = parser.parse_args(argv)
            _configure_logging(args.log_level)
            if args.command == "analyze":
                exit_code = _run_analyze(args)
            elif args.command == "replay":
                exit_code = _run_replay(args)
            elif args.command == "capture":
                exit_code = _run_capture(args)
            elif args.command == "serve":
                exit_code = _run_serve(args)
            elif args.command == "purge":
                exit_code = _run_purge(args)
            elif args.command == "start":
                exit_code = _run_start(args)
            elif args.command == "doctor":
                exit_code = _run_doctor(args)
            elif args.command == "scan":
                exit_code = _run_scan(args)
            elif args.command == "protect":
                exit_code = _run_protect(args)
            elif args.command == "demo":
                exit_code = _run_demo(args)
            elif args.command == "challenge":
                exit_code = _run_challenge(args)
            elif args.command == "export":
                exit_code = _run_export(args)
            elif args.command == "lab":
                exit_code = _run_lab(args)
            elif args.command == "inquire":
                exit_code = _run_inquire(args)
            elif args.command == "experiment":
                exit_code = _run_experiment(args)
            elif args.command == "eval-kit":
                exit_code = _run_eval_kit(args)
            elif args.command == "config":
                exit_code = _run_config(args)
            elif args.command == "share":
                exit_code = _run_share(args)
            elif args.command == "packs":
                exit_code = _run_packs(args)
            elif args.command == "studio":
                exit_code = _run_studio(args)
            elif args.command == "launch":
                exit_code = _run_launch(args)
            else:
                raise ValidationError(f"Unsupported command: {args.command}")

            try:
                _write_command_audit(args.command, args, exit_code)
            except Exception:  # pragma: no cover
                LOGGER.warning("Failed to write command audit", exc_info=True)
            return exit_code

        # Backward-compatible analyze mode: `python app.py --input ...`
        legacy_parser = _build_legacy_analyze_parser()
        args = legacy_parser.parse_args(argv)
        _configure_logging(args.log_level)
        return _run_analyze(args)

    except ValidationError as exc:
        LOGGER.error("Validation error: %s", exc)
        return EXIT_VALIDATION_ERROR
    except FileNotFoundError as exc:
        LOGGER.error("File error: %s", exc)
        return EXIT_FILE_ERROR
    except json.JSONDecodeError as exc:
        LOGGER.error("Invalid JSON: %s", exc)
        return EXIT_JSON_ERROR
    except Exception as exc:  # pragma: no cover
        LOGGER.exception("Unhandled error: %s", exc)
        return EXIT_GENERIC_ERROR


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
