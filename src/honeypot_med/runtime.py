"""Runtime config and optional engine enrichment utilities."""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_CONFIG = {
    "engine_mode": "auto",
    "remote_engine_url": None,
    "remote_auth_token": None,
    "remote_timeout_sec": 8,
    "remote_retries": 1,
    "allow_network": True,
    "asset_dir": "~/.honeypot-med/assets",
    "store_path": "~/.honeypot-med/data/events.jsonl",
    "audit_log_path": "~/.honeypot-med/logs/audit.jsonl",
    "last_bootstrap": None,
}



def _merge_dicts(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        merged[key] = value
    return merged



def _expand_path(raw: str) -> str:
    return str(Path(raw).expanduser())



def config_path_from(raw_path: str | None) -> Path:
    if raw_path:
        return Path(raw_path).expanduser()
    return Path("~/.honeypot-med/config.json").expanduser()



def load_runtime_config(raw_path: str | None = None) -> tuple[dict, Path]:
    path = config_path_from(raw_path)
    config = dict(DEFAULT_CONFIG)
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            config = _merge_dicts(config, raw)

    if config.get("remote_engine_url") in ("", "null"):
        config["remote_engine_url"] = None
    if config.get("remote_auth_token") in ("", "null"):
        config["remote_auth_token"] = None

    config["asset_dir"] = _expand_path(str(config["asset_dir"]))
    config["store_path"] = _expand_path(str(config["store_path"]))
    config["audit_log_path"] = _expand_path(str(config["audit_log_path"]))
    config["remote_timeout_sec"] = int(config.get("remote_timeout_sec", 8))
    config["remote_retries"] = int(config.get("remote_retries", 1))
    return config, path



def save_runtime_config(config: dict, raw_path: str | None = None) -> Path:
    path = config_path_from(raw_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(config)
    payload["asset_dir"] = _expand_path(str(payload["asset_dir"]))
    payload["store_path"] = _expand_path(str(payload["store_path"]))
    payload["audit_log_path"] = _expand_path(str(payload["audit_log_path"]))
    payload["remote_timeout_sec"] = int(payload.get("remote_timeout_sec", 8))
    payload["remote_retries"] = int(payload.get("remote_retries", 1))
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path



def ensure_runtime_dirs(config: dict) -> dict:
    asset_dir = Path(str(config["asset_dir"])).expanduser()
    store_path = Path(str(config["store_path"])).expanduser()
    audit_log_path = Path(str(config["audit_log_path"])).expanduser()
    asset_dir.mkdir(parents=True, exist_ok=True)
    store_path.parent.mkdir(parents=True, exist_ok=True)
    audit_log_path.parent.mkdir(parents=True, exist_ok=True)
    return {
        "asset_dir": str(asset_dir),
        "store_path": str(store_path),
        "audit_log_path": str(audit_log_path),
    }



def check_network(timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection(("huggingface.co", 443), timeout=timeout):
            return True
    except OSError:
        return False



def _selected_mode(mode: str, remote_url: str | None) -> str:
    if mode != "auto":
        return mode
    return "remote" if remote_url else "local"



def _severity_from_score(score: int, min_high_risk: int) -> str:
    if score >= 85:
        return "critical"
    if score >= min_high_risk:
        return "high"
    if score >= 35:
        return "medium"
    return "low"



def _apply_remote_adjustments(report: dict, adjustments: list[dict]) -> None:
    order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    events = report.get("events", [])

    for item in adjustments:
        if not isinstance(item, dict):
            continue
        idx = item.get("index")
        risk_delta = item.get("risk_delta")
        if not isinstance(idx, int) or not isinstance(risk_delta, int):
            continue
        if idx < 0 or idx >= len(events):
            continue

        event = events[idx]
        current = int(event.get("risk_score", 0))
        adjusted = max(0, min(100, current + risk_delta))

        # Keep evidence-first policy: no findings means no high/critical escalation.
        if int(event.get("finding_count", 0)) == 0 and adjusted >= 60:
            adjusted = min(adjusted, 59)

        event["risk_score"] = adjusted
        event["severity"] = _severity_from_score(adjusted, int(report["policy"]["min_high_risk"]))

    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for event in events:
        sev = str(event.get("severity", "low"))
        if sev not in severity_counts:
            sev = "low"
        severity_counts[sev] += 1

    report["severity_counts"] = severity_counts
    report["high_risk_count"] = severity_counts["critical"] + severity_counts["high"]



def enrich_report_with_engine(
    report: dict,
    payload: dict,
    *,
    mode: str,
    remote_url: str | None,
    remote_auth_token: str | None,
    allow_network: bool,
    timeout_sec: int = 8,
    retries: int = 1,
) -> dict:
    selected = _selected_mode(mode, remote_url)
    info = {
        "requested_mode": mode,
        "selected_mode": selected,
        "provider": "deterministic-local",
        "remote_url_configured": bool(remote_url),
        "network_allowed": allow_network,
        "remote_used": False,
        "fallback_reason": None,
    }

    if selected in {"remote", "hybrid"} and remote_url and allow_network:
        body = {
            "report": report,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        headers = {"Content-Type": "application/json"}
        if remote_auth_token:
            headers["Authorization"] = f"Bearer {remote_auth_token}"

        attempts = max(1, int(retries))
        last_error: str | None = None

        for _ in range(attempts):
            req = urllib.request.Request(
                remote_url,
                method="POST",
                data=json.dumps(body).encode("utf-8"),
                headers=headers,
            )

            try:
                with urllib.request.urlopen(req, timeout=timeout_sec) as resp:  # noqa: S310
                    raw = json.loads(resp.read().decode("utf-8"))
                if isinstance(raw, dict):
                    adjustments = raw.get("adjustments", [])
                    if isinstance(adjustments, list):
                        _apply_remote_adjustments(report, adjustments)
                    info["provider"] = str(raw.get("provider", "remote-http"))
                    info["remote_used"] = True
                    info["remote_summary"] = raw.get("summary")
                    last_error = None
                    break
                last_error = "remote response is not a JSON object"
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = f"remote engine unavailable: {exc}"

        if last_error:
            info["fallback_reason"] = last_error
            if selected == "remote":
                info["provider"] = "deterministic-local-fallback"

    elif selected in {"remote", "hybrid"} and not remote_url:
        info["fallback_reason"] = "remote mode requested but remote_url is not configured"
    elif selected in {"remote", "hybrid"} and not allow_network:
        info["fallback_reason"] = "remote mode requested but network is disabled"

    report["engine"] = info
    return report
