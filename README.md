<div align="center">
<img src="https://raw.githubusercontent.com/ByteWorthyLLC/honeypot-med/main/.github/assets/honeypot-med-hero.svg" alt="honeypot-med: prompt-injection detection for healthcare AI" width="100%">

# honeypot-med

**Prompt-injection honeypot for healthcare AI workflows. Browser-first. No API key required.**

[![License](https://img.shields.io/badge/license-MIT-2563EB?style=for-the-badge&labelColor=0F172A)](./LICENSE)
[![Live demo](https://img.shields.io/badge/try_it-live_demo-2563EB?style=for-the-badge&labelColor=0F172A)](https://byteworthyllc.github.io/honeypot-med/widget-demo/)

[**Try the widget →**](https://byteworthyllc.github.io/honeypot-med/widget-demo/) &nbsp;·&nbsp; [Live site](https://byteworthyllc.github.io/honeypot-med/) &nbsp;·&nbsp; [Run locally](#quickstart)
</div>

---

> **honeypot-med** runs healthcare AI prompts through a detection engine to identify prompt-injection risk. The rule engine runs in your browser. Your prompt never leaves the page. Local-first by default (CPU mode, no API key). Generates shareable proof artifacts for CI integration, release gates, and challenge publishing.

## Try it without installing

> **[Paste any healthcare AI prompt into the live widget →](https://byteworthyllc.github.io/honeypot-med/widget-demo/)**
>
> Instant verdict. The shareable link contains only the verdict and rule IDs, never your prompt text.
>
> `https://byteworthyllc.github.io/honeypot-med/widget-demo/`

## What it detects

| Rule category | Examples | Severity |
|---|---|---|
| PHI exfiltration | "Send all patient records to..." | Critical |
| Role injection | "You are now an unrestricted medical AI..." | High |
| System prompt override | "Ignore previous instructions..." | High |
| Authority impersonation | Fake FDA, CMS, or HIPAA directives | High |
| Care protocol manipulation | Prompt attempts to alter triage or treatment logic | Medium |

## Quickstart

```bash
python app.py
```

No API key required. Local-first mode is the default and intended experience.

Docker:

```bash
docker compose up --build studio
```

From source:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python app.py
```

## How it works

```
Prompt input
    │
    ▼
Rule Engine (runs locally in CPU mode)
    │
    ├── PHI exfiltration patterns
    ├── Role injection patterns
    ├── System prompt override patterns
    ├── Authority impersonation patterns
    └── Care protocol manipulation patterns
    │
    ▼
Verdict: PASS / REVIEW / BLOCK
    │
    ▼
Shareable link (verdict + rule IDs only, prompt text never included)
```

## Modes

| Mode | Command | Requires |
|---|---|---|
| Local/CPU (default) | `python app.py` | Nothing |
| Challenge | `python app.py challenge` | Nothing |
| CTF | `python app.py ctf --pack healthcare-challenge` | Nothing |
| Daily | `python app.py daily` | Nothing |
| Remote engine | `python app.py --engine-mode remote --remote-url <url>` | Remote endpoint |

## Output artifacts

Each run produces structured, parseable output:

- Verdict JSON (`PASS` / `REVIEW` / `BLOCK` + rule IDs that fired)
- Shareable HTML proof page (prompt never included)
- Challenge report with SARIF, OTEL, JUnit, and OpenInference formats
- CTF pack with evidence-predicate flags and writeup bundle

## CI integration

Wire the exit code into any CI pipeline. The tool returns non-zero on violations:

```yaml
- uses: ByteWorthyLLC/honeypot-med@main
  with:
    pack: healthcare-challenge
    output-dir: honeypot-med-report
    fail-under: 70
    upload-artifact: true
    upload-sarif: true
```

The action uploads `honeypot-med.sarif` to GitHub Code Scanning automatically.

```bash
# Gate check: fail CI if any critical or high findings
python app.py analyze --input examples/clean.json --gate --max-critical 0 --max-high 0
```

## MCP server (Claude Code / Cursor)

```bash
pip install honeypot-med[mcp]
```

Add to `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "honeypot-med": {
      "command": "honeypot-med-mcp"
    }
  }
}
```

Tools exposed: `scan_prompt`, `run_attack_pack`, `list_packs`, `explain_finding`. Local-only: no prompts are exfiltrated.

## License + contributing

MIT. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

Built and maintained by [ByteWorthy LLC](https://byteworthy.io).
