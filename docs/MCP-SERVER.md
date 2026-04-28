# Honeypot Med MCP Server

The Honeypot Med MCP (Model Context Protocol) server brings the local
prompt-injection rule engine inside every Claude Code, Cursor, or other
MCP-aware coding session. Once registered, your agent can scan a prompt,
run a healthcare attack pack, list packs, and look up the OWASP / NIST
anchor for any fired rule - all locally, with no API keys and no
prompt exfiltration.

## Install

```bash
pip install honeypot-med[mcp]
```

This installs the `honeypot-med-mcp` console entry point.

## Configure (Claude Code)

Add the server to your Claude Code MCP config. Either user-wide
(`~/.claude/mcp.json`) or per-project (`.mcp.json` at the repo root):

```json
{
  "mcpServers": {
    "honeypot-med": {
      "command": "honeypot-med-mcp"
    }
  }
}
```

Restart Claude Code. The four tools below become available in every
session.

## Configure (Cursor / other MCP clients)

Use the same pattern - point the MCP client at the `honeypot-med-mcp`
binary on your `PATH`. The transport is stdio.

## Tool reference

| Tool | What it does |
|------|--------------|
| `scan_prompt(prompt)` | Run a single prompt through the local rule engine. Returns `verdict` (PASS / REVIEW / BLOCK), severity counts, and per-rule findings with plain-English context. |
| `run_attack_pack(pack_name)` | Run every prompt in a bundled healthcare pack (e.g. `prior-auth`, `claims`, `triage`) through the engine. Returns the worst-case verdict and a summary. |
| `list_packs()` | List the bundled attack packs available to `run_attack_pack`, each with `name`, `attack_count`, and a domain label. |
| `explain_finding(rule_id)` | Look up a fired rule_id (e.g. `INJ-001`) and return plain English, the OWASP LLM01 anchor, the NIST AI 600-1 anchor, and a healthcare-appropriate mitigation. |

## What the server does NOT do

- It never calls an external service. The engine, the packs, and the
  explanations are all local.
- It does not capture or store PHI. Prompts are evaluated against
  regex-based rules in memory and discarded.
- It does not give medical advice. Mitigations are security guidance
  only.
- It does not modify your files or your agent's tools. It is read-only
  analysis.

## Healthcare and compliance notes

Every explained finding cites:

- **OWASP LLM01:2025 - Prompt Injection** ([OWASP LLM Top 10](https://genai.owasp.org/llmrisk/llm01-prompt-injection/))
- **NIST AI 600-1 - Generative AI Profile of the AI Risk Management
  Framework** ([NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf))

Use the verdict and findings as input to your own review, not as a
substitute for clinical or compliance judgement. Honeypot Med is a
local-first proof tool, not a medical device, and not a HIPAA business
associate.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `honeypot-med MCP server requires the 'mcp' package` | Run `pip install honeypot-med[mcp]`. |
| `Unknown pack '<name>'` | Call `list_packs` to see the available pack names. |
| Tool absent in Claude Code | Confirm the MCP config path, then fully restart the Claude Code app. |

## Source

The server lives at `src/honeypot_med/mcp_server.py`. The rule engine it
wraps lives at `src/honeypot_med/service.py`. Attack packs are bundled
JSON files at `src/honeypot_med/packs/`.
