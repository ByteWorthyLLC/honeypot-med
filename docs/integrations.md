# Integrations

Honeypot Med now exports both human-facing and machine-facing artifacts.

## GitHub Action

The root `action.yml` is a composite GitHub Action:

```yaml
- uses: ByteWorthyLLC/honeypot-med@main
  with:
    pack: healthcare-challenge
    # Or use: input-file: examples/sample.json
    output-dir: honeypot-med-report
    fail-under: 70
    upload-artifact: true
    upload-sarif: true
```

The action installs the package, runs challenge mode, uploads the generated artifact directory, and can upload SARIF to GitHub Code Scanning.

## CLI Exports

Generate all portable formats:

```bash
python app.py export --pack claims --format all --outdir reports/export
```

Generate one format:

```bash
python app.py export --pack claims --format sarif --outdir reports/sarif
python app.py export --pack claims --format otel --outdir reports/otel
python app.py export --pack claims --format badge --outdir reports/badge
python app.py export --pack claims --format eval-kit --outdir reports/eval-kit
python app.py eval-kit --pack healthcare-challenge --outdir reports/eval-kit
```

## Eval Kit

The eval kit is for teams that already use file-based eval tooling and do not want another hosted system.

It writes:

- `eval-samples.jsonl`: canonical trap samples with `id`, `input`, `target`, and `metadata`
- `inspect-dataset.jsonl`: Inspect AI-compatible sample records
- `promptfoo-config.yaml`: promptfoo config that uses the no-network `echo` provider by default
- `promptfoo-tests.json`: promptfoo test cases for existing provider configs
- `openai-evals.yaml`: legacy open-source OpenAI Evals registry entry
- `openai-evals-samples.jsonl`: simple `input`, `ideal`, and `metadata` JSONL records
- `eval-kit.md`: local usage notes

## Formats

- HTML: public proof page
- SVG badge: README and docs embeds
- SVG social card: launch posts and screenshots
- Specimen codex: memorable report taxonomy for human review
- Trap ledger CSV: spreadsheet and notebook workflows
- Field guide: narrative lab artifact for founders, security teams, and launch posts
- Inquiry notebook: curiosity-first questions and local experiment prompts
- Unknown ledger CSV: follow-up queue for silent passes and unproven hypotheses
- Counterfactual prompts: deterministic authority-costume and safety-boundary prompt mutations
- Experiment matrix: one-variable-at-a-time research plan
- Question atlas: reusable research questions linked to report events
- Ablation ladder CSV: evidence-depth checklist for proving or falsifying findings
- Eval kit: promptfoo, Inspect AI, OpenAI Evals, and canonical JSONL adapters
- Offline proof: simple assurance that the default path requires no API keys or paid service
- SARIF: static-analysis/code-scanning workflows
- OpenTelemetry logs: telemetry-style ingestion and observability workflows
- JSON: dashboards and custom integrations
- Markdown: PR comments, release notes, and docs
