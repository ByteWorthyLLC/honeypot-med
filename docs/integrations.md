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

The action installs the package, runs challenge mode, appends `github-summary.md` to the workflow step summary, uploads the generated artifact directory, and can upload SARIF to GitHub Code Scanning.

## CLI Exports

Generate all portable formats:

```bash
python app.py export --pack claims --format all --outdir reports/export
```

Generate one format:

```bash
python app.py export --pack claims --format sarif --outdir reports/sarif
python app.py export --pack claims --format otel --outdir reports/otel
python app.py export --pack claims --format junit --outdir reports/junit
python app.py export --pack claims --format png --outdir reports/png
python app.py export --pack claims --format github-summary --outdir reports/summary
python app.py export --pack claims --format openinference --outdir reports/openinference
python app.py export --pack claims --format langsmith --outdir reports/langsmith
python app.py export --pack claims --format casebook --outdir reports/casebook
python app.py export --pack claims --format badge --outdir reports/badge
python app.py export --pack claims --format eval-kit --outdir reports/eval-kit
python app.py eval-kit --pack healthcare-challenge --outdir reports/eval-kit
python app.py eval-kit verify --dir reports/eval-kit
python app.py hf-mirror plan --outdir reports/hf-mirror
python app.py release-kit --source-dir reports/export --outdir dist/release-bundles --name claims-export
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
- `README.dataset-card.md`: Hugging Face-ready dataset card text
- `system-card.md`: local system card for the evaluated workflow
- `hf-artifact-manifest.md`: Hugging Face packaging manifest
- `eval-kit.md`: local usage notes

## Formats

- HTML: public proof page
- Visual proof dossier: aesthetic print-friendly HTML for stakeholders
- Offline proof PDF: no-API proof document generated locally
- UI mockup: static product surface generated from a run
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
- Hugging Face cards: dataset card, system card, and artifact manifest generated locally
- Casebook: redacted forensic HTML, JSON, traparium, unknowns page, failure recipes, trap tree, and notebook
- PNG cards: raster social card and badge for places that do not render SVG reliably
- Release kit: zip archive, SHA-256 checksum file, release notes, and manifest
- Offline proof: simple assurance that the default path requires no API keys or paid service
- SARIF: static-analysis/code-scanning workflows
- JUnit XML: CI test report ingestion
- GitHub summary: step summary Markdown for Actions
- OpenTelemetry logs: telemetry-style ingestion and observability workflows
- OpenInference traces: offline JSONL trace rows
- LangSmith runs: offline JSONL run rows
- JSON: dashboards and custom integrations
- Markdown: PR comments, release notes, and docs

## Hugging Face Mirror Planning

`hf-mirror plan` writes a manifest and notes for candidate public datasets. It does not download anything. Use `hf-mirror fetch` only after reviewing upstream licenses and installing `huggingface_hub`.
