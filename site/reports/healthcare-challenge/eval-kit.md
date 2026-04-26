# Honeypot Med Healthcare AI Challenge Eval Kit

This directory is generated locally by Honeypot Med. It contains adapter files for moving the same trap set into other eval workflows without paying for a hosted service.

## Files

- `eval-samples.jsonl`: canonical JSONL with `id`, `input`, `target`, and `metadata`.
- `inspect-dataset.jsonl`: Inspect AI-compatible sample shape with `input`, `target`, `id`, and `metadata`.
- `promptfoo-config.yaml`: promptfoo config that uses the no-network `echo` provider by default.
- `promptfoo-tests.json`: promptfoo test cases separated from config for teams that already have providers configured.
- `openai-evals.yaml`: legacy open-source OpenAI Evals registry entry pointing at `openai-evals-samples.jsonl`.
- `openai-evals-samples.jsonl`: simple `input` and `ideal` records for legacy eval import.

## Local Commands

```bash
promptfoo eval -c promptfoo-config.yaml
```

## Notes

- Source: `pack:healthcare-challenge`
- Default generated artifacts do not call model APIs.
- Replace the echo provider only when you intentionally want to run live model comparisons.
