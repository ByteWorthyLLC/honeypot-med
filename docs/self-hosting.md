# Self-Hosting

`honeypot-med` now supports zero-code self-hosting through Docker.

## Studio

Launch the browser experience:

```bash
docker compose up --build studio
```

Then open:

```text
http://127.0.0.1:8899
```

The studio container persists state in the `honeypot_med_home` volume under `/home/honeypot/.honeypot-med/`.

## Capture Service

Launch the decoy capture API:

```bash
docker compose up --build capture
```

Health endpoint:

```bash
curl http://127.0.0.1:8787/health
```

## Runtime Knobs

Useful environment variables:

- `HONEYPOT_MED_STUDIO_PORT`
- `HONEYPOT_MED_CAPTURE_PORT`
- `HONEYPOT_MED_STORE_PATH`
- `HONEYPOT_MED_HEALTHCHECK_URL`

## One-Off Commands

Use the container image directly:

```bash
docker build -t honeypot-med:local .
docker run --rm honeypot-med:local doctor
docker run --rm honeypot-med:local packs --json
```

## Notes

- The default container mode is `studio`.
- Health checks are built into the image.
- The image runs as a non-root user.

