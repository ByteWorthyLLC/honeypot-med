# Launch Readiness

`honeypot-med readiness` verifies the repo has the launch-critical pieces that should not silently drift:

- governance files
- GitHub workflows
- local runtime files
- public site pages
- generated healthcare challenge visual packet
- free/local-first copy
- no public vanity artifact patterns

Run:

```bash
python app.py readiness --strict
```

Write reports:

```bash
python app.py readiness --outdir reports/readiness
```

Outputs:

- `launch-readiness.json`
- `launch-readiness.md`

`--strict` returns a non-zero exit code if any required surface is missing. The command does not call APIs, does not need Railway, and does not require paid services.
