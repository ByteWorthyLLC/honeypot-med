# Studio

`honeypot-med studio` launches a local browser-based review experience on `127.0.0.1:8899` by default.

## What it does

- accepts a pasted prompt or a bundled attack pack
- analyzes the payload using the same core engine as the CLI
- creates a share bundle for each run
- serves the generated HTML, PDF, SVG, JSON, and Markdown artifacts locally

## Commands

```bash
python app.py studio
python app.py studio --host 127.0.0.1 --port 9000 --no-open-browser
```

## HTTP Routes

- `GET /`: hosted UI
- `GET /health`: runtime health summary
- `GET /api/packs`: bundled pack metadata
- `POST /api/analyze`: create verdict bundle from `prompt` or `pack`
- `GET /bundles/<id>/<file>`: serve generated bundle artifacts

## Bundle Location

Studio bundles are stored under:

- `~/.honeypot-med/assets/studio-bundles/`

Each analyze request creates a timestamped bundle directory.
