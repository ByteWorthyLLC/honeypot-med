# Runbook

## 1. Service Down

1. Check process and port bind (`python app.py serve ...`).
2. Hit `/health` locally.
3. Check file permissions for event store path.
4. Restart service and capture logs.

## 2. Gate Failures in CI

1. Reproduce locally with `scripts/security/honeypot-gate.sh`.
2. Inspect findings JSON and markdown report.
3. If expected and reviewed, add temporary suppression with expiry in `.honeypot-baseline.json`.
4. If unexpected, treat as active incident and patch rules/runtime.

## 3. Data Redaction Concerns

1. Run test suite (`python -m unittest discover ...`).
2. Verify `redaction_hits` and `redaction_status` in captured events.
3. Patch redaction patterns and re-run replay fixtures.

## 4. Store Growth / Retention

1. Run dry-run purge: `python app.py purge --store data/events.jsonl --days 30`.
2. Apply purge: `python app.py purge --store data/events.jsonl --days 30 --apply`.
3. Confirm backups before destructive retention runs.
