# Rollback Plan

## Scope

Rollback focuses on local/self-hosted runtime and JSONL store artifacts.

## Procedure

1. Stop running service process.
2. Restore previous code/package version (previous git tag/release artifact).
3. Restore event store backup if schema incompatibility occurred.
4. Re-run health check and baseline gate.

## Store Backup/Restore

Backup:

```bash
cp data/events.jsonl data/events.jsonl.bak
```

Restore:

```bash
cp data/events.jsonl.bak data/events.jsonl
```

## Validation After Rollback

```bash
python app.py analyze --input examples/clean.json --gate --max-critical 0 --max-high 0 --max-unproven 0
python app.py replay --store examples/replay-fixture.jsonl --pretty
```

## Failure Escalation

- If rollback fails, move to maintenance mode and preserve logs/store for forensics.
