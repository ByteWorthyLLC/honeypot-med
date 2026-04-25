# Viral Product Notes

## Core Hook

Honeypot Med should not be sold as a generic security scanner.
It should be framed as:

`Paste your AI workflow prompt. Get an investor-ready or buyer-ready security verdict in under a minute.`

## Product Loops

1. Paste-to-verdict loop
Users try one suspicious prompt and get an immediate result without building JSON payloads.

2. Verdict-page loop
Every scan can become a standalone HTML artifact that is easy to forward internally, attach to deals, or post publicly.

3. Demo-loop
`honeypot-med demo` generates sample artifacts so the product always has something visually persuasive to show.

4. Studio-loop
`honeypot-med studio` gives non-developers a browser flow for prompt review, packs, and exports.

5. Pack-loop
Bundled healthcare attack packs let users test real categories without crafting their own payloads.

## Launch Angles

1. "We tested healthcare AI prompts that should never ship."
2. "Security proof pages for AI startups."
3. "The Stripe checkout experience for prompt-injection risk reviews."

## Implemented

1. Hosted local studio flow
2. PDF and SVG social-card export
3. Curated healthcare attack packs
4. Branded visual identity using generated art
5. Recent bundle gallery inside the studio
6. Docker self-hosting path for non-developers
7. Release trust artifacts with checksums and manifest output
8. One-command free local launch via `python app.py`

## What To Prioritize Next

1. Add a public gallery of sanitized example verdict pages.
2. Add one-click PNG raster export for the social card.
3. Add more domain packs: utilization management, appeals, eligibility, intake bots.
4. Add hosted deployment templates for Fly.io, Railway, and Render instead of Docker-only self-hosting.
