# Alerts

## Critical

- Capture endpoint unavailable for 5m
- Gate check fails on main branch
- Replay job exits non-zero for 3 consecutive runs

## High

- p95 capture latency > 250ms for 15m
- Store write failures > 1% over 10m
- Redaction failures detected in tests or runtime exceptions

## Medium

- Event volume drops > 80% day-over-day
- Purge job skipped for > 48h

## Routing

- Critical/High: pager + Slack + ticket
- Medium: ticket + daily review queue
