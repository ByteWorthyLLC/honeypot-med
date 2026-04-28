"""MCP (Model Context Protocol) server for honeypot-med.

Exposes the local prompt-injection rule engine inside Claude Code, Cursor, and
any other MCP-aware client. Once installed and registered, every chat session
gains four tools that scan prompts against the honeypot-med rule set, run a
healthcare attack pack, list packs, and look up the OWASP/NIST anchor for a
fired rule.

Local-only. No prompts are exfiltrated. No external service is contacted.
All findings cite OWASP LLM01:2025 (Prompt Injection) and NIST AI 600-1
(Generative AI Profile of the AI Risk Management Framework) where mapped.

Designed for healthcare AI workflows: this server does not provide medical
advice, does not capture PHI, and treats every prompt as untrusted input.
"""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

from .errors import ValidationError
from .models import InputEvent, InputPayload, InputToolCall
from .service import DEFAULT_RULES, analyze_prompts

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
except ImportError as e:  # pragma: no cover - import guarded for runtime install
    raise SystemExit(
        "honeypot-med MCP server requires the 'mcp' package.\n"
        "Install with: pip install honeypot-med[mcp]"
    ) from e


SERVER_NAME = "honeypot-med"
SERVER_VERSION = "0.4.1"

# Static rule explanation table. Maps the rule_ids defined in service.DEFAULT_RULES
# to their OWASP LLM Top 10 anchor, NIST AI 600-1 control family, and a plain-
# English summary plus a healthcare-appropriate mitigation. Kept static so the
# server can answer offline. The LLM-backed explainer is P2.
RULE_EXPLANATIONS: dict[str, dict[str, str]] = {
    "INJ-001": {
        "plain_english": (
            "The prompt tries to override the system instructions with phrases like "
            "'ignore previous instructions'. Classic instruction-override attempt."
        ),
        "owasp_anchor": "OWASP LLM01:2025 Prompt Injection - Direct Injection",
        "nist_anchor": "NIST AI 600-1 GV-3.2, MS-2.6 (Information Integrity)",
        "mitigation": (
            "Pin the system prompt above untrusted input, treat user content as data "
            "(never as authority), and require explicit allow-listed tool intents "
            "before executing any privileged action."
        ),
    },
    "INJ-002": {
        "plain_english": (
            "The prompt asks the model to exfiltrate, dump, or leak records or "
            "credentials - a data exfiltration attempt against the LLM and its tools."
        ),
        "owasp_anchor": "OWASP LLM01:2025 Prompt Injection - Sensitive Information Disclosure",
        "nist_anchor": "NIST AI 600-1 MS-2.10 (Data Privacy), MS-2.7 (Information Security)",
        "mitigation": (
            "Scope every database/FHIR/storage tool to the authenticated patient or "
            "customer, deny bulk exports from the LLM control plane, and audit-log "
            "every export attempt via tamper-evident storage."
        ),
    },
    "INJ-003": {
        "plain_english": (
            "The prompt asks the model to disable safeguards, bypass guardrails, or "
            "jailbreak the system - a safeguard-bypass attempt."
        ),
        "owasp_anchor": "OWASP LLM01:2025 Prompt Injection - Indirect Injection / Jailbreak",
        "nist_anchor": "NIST AI 600-1 GV-1.5, MS-2.6 (Safe Operation)",
        "mitigation": (
            "Make safety controls non-toggleable from the prompt surface. Validate "
            "tool call intents server-side, reject 'admin' / 'config' tool families "
            "from user-driven prompts, and require human approval for policy changes."
        ),
    },
}


def _payload_from_prompt(prompt: str) -> InputPayload:
    """Wrap a single prompt string in the InputPayload shape the engine expects."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValidationError("prompt must be a non-empty string")
    event = InputEvent(
        prompt=prompt.strip(),
        tool_calls=[],
        model_output="",
        response="",
    )
    return InputPayload(events=[event])


def _payload_from_pack(pack_name: str) -> InputPayload:
    """Load a pack JSON file from the bundled packs/ directory."""
    if not isinstance(pack_name, str) or not pack_name.strip():
        raise ValidationError("pack_name must be a non-empty string")
    safe_name = pack_name.strip()
    if "/" in safe_name or ".." in safe_name:
        raise ValidationError("pack_name must be a bare filename without path components")

    packs_root = resources.files("honeypot_med").joinpath("packs")
    pack_path = packs_root.joinpath(f"{safe_name}.json")
    try:
        raw = json.loads(pack_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        available = sorted(
            p.name.removesuffix(".json")
            for p in packs_root.iterdir()
            if p.name.endswith(".json") and p.name != "manifest.json"
        )
        raise ValidationError(
            f"Unknown pack '{safe_name}'. Available: {', '.join(available)}"
        ) from exc
    return InputPayload.from_dict(raw)


def _domain_for_pack(name: str) -> str:
    """Infer a short domain label from a pack filename."""
    return name.replace("_", " ").replace("-", " ").strip()


def _scan_prompt_tool(prompt: str) -> dict[str, Any]:
    payload = _payload_from_prompt(prompt)
    report = analyze_prompts(payload, rules=DEFAULT_RULES)
    severity_counts = report["severity_counts"]
    verdict = "BLOCK"
    if severity_counts["critical"] == 0 and severity_counts["high"] == 0:
        verdict = "REVIEW" if severity_counts["medium"] > 0 else "PASS"

    findings = []
    for event_report in report["events"]:
        for finding in event_report["findings"]:
            rule_id = finding["rule_id"]
            findings.append(
                {
                    "rule_id": rule_id,
                    "attack_family": finding["attack_family"],
                    "severity": finding["severity"],
                    "score": finding["score"],
                    "proven": finding["proven"],
                    "plain_english": RULE_EXPLANATIONS.get(rule_id, {}).get(
                        "plain_english",
                        "No static explanation available for this rule yet.",
                    ),
                }
            )

    return {
        "verdict": verdict,
        "severity_counts": severity_counts,
        "findings": findings,
        "rule_count": len(DEFAULT_RULES),
        "note": "Local-only scan. No prompts are exfiltrated. OWASP LLM01:2025 / NIST AI 600-1 anchored.",
    }


def _run_attack_pack_tool(pack_name: str) -> dict[str, Any]:
    payload = _payload_from_pack(pack_name)
    report = analyze_prompts(payload, rules=DEFAULT_RULES)
    severity_counts = report["severity_counts"]
    if severity_counts["critical"] > 0 or severity_counts["high"] > 0:
        verdict = "BLOCK"
    elif severity_counts["medium"] > 0:
        verdict = "REVIEW"
    else:
        verdict = "PASS"

    findings_count = sum(int(event.get("finding_count", 0)) for event in report["events"])
    return {
        "pack_name": pack_name,
        "verdict": verdict,
        "summary": severity_counts,
        "findings_count": findings_count,
        "attack_count": report["total_prompts"],
        "proven_findings_count": report["proven_findings_count"],
        "note": "Worst severity wins for the pack verdict. Local-only run.",
    }


def _list_packs_tool() -> list[dict[str, Any]]:
    packs_root = resources.files("honeypot_med").joinpath("packs")
    out: list[dict[str, Any]] = []
    for entry in sorted(packs_root.iterdir(), key=lambda p: p.name):
        if not entry.name.endswith(".json") or entry.name == "manifest.json":
            continue
        name = entry.name.removesuffix(".json")
        try:
            raw = json.loads(entry.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        events = raw.get("events", []) if isinstance(raw, dict) else []
        out.append(
            {
                "name": name,
                "attack_count": len(events) if isinstance(events, list) else 0,
                "domain": _domain_for_pack(name),
            }
        )
    return out


def _explain_finding_tool(rule_id: str) -> dict[str, Any]:
    if not isinstance(rule_id, str) or not rule_id.strip():
        raise ValidationError("rule_id must be a non-empty string")
    key = rule_id.strip().upper()
    explanation = RULE_EXPLANATIONS.get(key)
    if explanation is None:
        return {
            "rule_id": key,
            "plain_english": "No static explanation registered for this rule_id yet.",
            "owasp_anchor": "OWASP LLM01:2025 Prompt Injection (general)",
            "nist_anchor": "NIST AI 600-1 (Generative AI Profile)",
            "mitigation": (
                "Treat the prompt surface as untrusted input. Pin system prompts, "
                "scope tools to the authenticated user, and audit-log privileged calls."
            ),
            "note": "Healthcare-appropriate guidance only. No medical advice given.",
        }
    return {
        "rule_id": key,
        **explanation,
        "note": "Healthcare-appropriate guidance only. No medical advice given.",
    }


def _build_server() -> Server:
    server: Server = Server(SERVER_NAME)

    @server.list_tools()
    async def _list_tools() -> list[Tool]:
        return [
            Tool(
                name="scan_prompt",
                description=(
                    "Scan a single prompt against the honeypot-med rule engine. "
                    "Returns verdict (PASS/REVIEW/BLOCK), severity counts, and per-rule findings "
                    "with OWASP LLM01 / NIST AI 600-1 anchored plain-English context. Local-only."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The prompt text to evaluate. Treated as untrusted input.",
                        }
                    },
                    "required": ["prompt"],
                },
            ),
            Tool(
                name="run_attack_pack",
                description=(
                    "Run a bundled healthcare attack pack (claims, prior-auth, triage, intake, "
                    "appeals, eligibility, utilization-management, healthcare-challenge) through "
                    "the rule engine. Returns the worst-case verdict and summary. Local-only."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pack_name": {
                            "type": "string",
                            "description": "Pack filename without .json (e.g. 'prior-auth').",
                        }
                    },
                    "required": ["pack_name"],
                },
            ),
            Tool(
                name="list_packs",
                description=(
                    "List the bundled attack packs available to run_attack_pack. "
                    "Each entry has a name, attack_count, and inferred domain label."
                ),
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="explain_finding",
                description=(
                    "Explain a fired rule_id (e.g. INJ-001) with plain English, the OWASP LLM01 "
                    "anchor, the NIST AI 600-1 anchor, and a healthcare-appropriate mitigation. "
                    "Static lookup - no medical advice, no PHI handling."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "rule_id": {
                            "type": "string",
                            "description": "Rule identifier returned by scan_prompt (e.g. 'INJ-001').",
                        }
                    },
                    "required": ["rule_id"],
                },
            ),
        ]

    @server.call_tool()
    async def _call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        try:
            if name == "scan_prompt":
                result = _scan_prompt_tool(prompt=str(arguments.get("prompt", "")))
            elif name == "run_attack_pack":
                result = _run_attack_pack_tool(pack_name=str(arguments.get("pack_name", "")))
            elif name == "list_packs":
                result = _list_packs_tool()
            elif name == "explain_finding":
                result = _explain_finding_tool(rule_id=str(arguments.get("rule_id", "")))
            else:
                raise ValidationError(f"Unknown tool '{name}'")
        except ValidationError as exc:
            error_payload = {"error": "validation_error", "message": str(exc)}
            return [TextContent(type="text", text=json.dumps(error_payload, indent=2))]
        except Exception as exc:  # pragma: no cover - defensive
            error_payload = {"error": "internal_error", "message": str(exc)}
            return [TextContent(type="text", text=json.dumps(error_payload, indent=2))]

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    return server


async def _run() -> None:
    server = _build_server()
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    """MCP server entry point. Run via: python -m honeypot_med.mcp_server or honeypot-med-mcp."""
    import asyncio

    asyncio.run(_run())


if __name__ == "__main__":
    main()
