# SLO

## Service Objectives

- API availability: 99.5% monthly
- Capture endpoint p95 latency: < 250ms for 1MB max request body
- Replay completion: < 60s for 10k events on reference hardware

## Error Budget

- Monthly downtime budget at 99.5%: 3h 39m
- Budget breach action: freeze feature rollout and prioritize reliability fixes

## Measurement

- Availability measured from `/health` probes.
- Latency measured at reverse-proxy or application middleware.
- Replay duration measured from CLI run telemetry in CI and cron jobs.
