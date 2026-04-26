# Contributing

## What Helps Most

High-leverage contributions for this project:

- new attack packs grounded in real healthcare workflows
- new challenge packs and baseline profiles
- new integrations and export adapters
- new report templates, badges, and social-card layouts
- false-positive reduction for prompt injection findings
- UI polish for the hosted studio
- packaging and installer reliability
- docs that make the project easier for non-developers to run

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python app.py doctor
```

## Validation Before Opening a PR

```bash
python -m py_compile app.py src/honeypot_med/*.py
python -m unittest discover -s tests -p 'test_*.py'
python app.py share --pack claims --outdir reports/share-check
python app.py challenge --outdir reports/challenge-check
python app.py export --pack claims --format all --outdir reports/export-check
```

If you changed packaging or deployment surfaces, also run:

```bash
python scripts/release/generate-manifest.py
```

## Pull Request Guidance

- keep changes focused
- explain the user-facing behavior change
- include tests when behavior changes
- do not break local-first defaults
- do not add hidden telemetry

## Attack Pack Proposals

If you want to contribute a new attack pack, use the GitHub issue template for attack pack proposals and include:

- the healthcare workflow being modeled
- the attacker objective
- expected indicators or tool-call patterns
- why the scenario is not already covered

## Contributor Quests

The highest-leverage contribution paths are intentionally concrete:

- Add a pack: include a realistic healthcare workflow, update `manifest.json`, and add one copy-ready command.
- Add an integration: export or ingest a format teams already use, such as traces, telemetry, PR comments, or dashboard JSON.
- Add a report template: make generated artifacts more readable, more screenshot-ready, or more useful for buyers.
- Add a benchmark: contribute a baseline profile or challenge pack that makes scores easier to compare.
