# Honeypot Med Healthcare AI Challenge System Card

This is a local system card for a Honeypot Med run. It documents the evaluated workflow shape without requiring hosted telemetry.

## Evaluation Scope

- Source: `pack:healthcare-challenge`
- Domain: healthcare AI prompt-injection traps
- Default network behavior: no API calls required
- Output artifacts: report JSON, HTML, SARIF, JUnit, eval adapters, observability JSONL, casebook

## Safety Boundary

Honeypot Med flags prompt-injection evidence and suspicious workflow behavior. It is not a clinical validation suite.

## Observed Result

- Total prompts: 10
- High-risk events: 2
- Proven findings: 3
