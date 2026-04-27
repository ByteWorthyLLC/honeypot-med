# Studio

`honeypot-med studio` launches a local browser-based review experience on `127.0.0.1:8899` by default.

## What it does

- accepts a pasted prompt or a bundled attack pack
- analyzes the payload using the same core engine as the CLI
- creates a share bundle for each run
- serves generated HTML, PDF, SVG, PNG, JSON, Markdown, CSV, and XML artifacts locally
- surfaces the visual proof dossier, offline proof PDF, generated UI mockup, share page, executive PDF, social card, and launch kit directly in the result panel
- keeps recent bundles browseable with direct Dossier, PDF, Mockup, and Share links

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

## Visual Outputs

Every Studio run now creates:

- `proof-dossier.html`: aesthetic proof page with print-friendly styling
- `offline-proof.pdf`: no-API proof document suitable for attachments
- `ui-mockup.html`: static product mockup generated from the run
- `index.html`: public share page
- `summary.pdf`: executive report brief
- `social-card.svg` and `social-card.png`: visual assets for docs and posts
