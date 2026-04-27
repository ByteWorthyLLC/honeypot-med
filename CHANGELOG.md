# Changelog

## 0.4.1 - 2026-04-26

### Added
- Visual proof packet generation for every share/challenge/lab bundle: `proof-dossier.html`, `offline-proof.pdf`, and `ui-mockup.html`.
- Studio result cards and recent-bundle gallery links for the visual dossier, offline proof PDF, UI mockup, share page, social card, and launch kit.
- Public report-gallery links and regenerated healthcare challenge sample artifacts for the new visual packet outputs.
- `readiness` command for launch-critical repo, site, workflow, copy, and generated artifact checks.

### Changed
- README, docs, launch copy, FAQ, media kit, public site, and generated launch kits now describe the visual proof packet instead of only plain proof text.
- Self-hosting docs explicitly keep Railway and other hosted environments optional; the default product remains local-first and free.

## 0.4.0 - 2026-04-25

### Added
- Built-in bundle metadata (`bundle.json`) and a recent-bundles gallery in the hosted studio.
- Docker image, Compose self-hosting path, container entrypoint, and built-in health check.
- Release manifest generator for `dist/release-manifest.json` and `dist/SHA256SUMS.txt`.
- Open source community health files: `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue templates, and PR template.
- One-command local launch path via `python app.py`, `run.sh`, `run.ps1`, and `run.bat`.
- GitHub automation for Docker smoke tests, CodeQL scanning, and Dependabot updates.
- Support guide and release-manifest unit coverage.
- A public releases and installers page on GitHub Pages with bootstrap commands and release hydration from the GitHub API.
- New search surfaces for prior authorization, evals vs proof bundles, and guardrails vs launch review.
- A dedicated 404 page for the public product surface.

### Changed
- CI now byte-compiles the codebase and smoke-tests share bundle generation.
- Packaging CI now smoke-tests packaged binaries before uploading artifacts.
- CLI help and default entry behavior now prioritize the browser studio instead of legacy analyze mode.
- Studio now supports prompt chips, keyboard submission, and clearer launch/release navigation.
- Share bundles now include release/install copy so non-developers have a cleaner path from proof page to install.
- Release publishing now creates GitHub releases from tag builds and publishes aggregated checksums and a manifest.

## 0.3.0 - 2026-04-24

### Added
- Beginner-friendly commands: `start`, `doctor`, `scan`, `protect`, `demo`.
- Runtime config command group: `config show`, `config set`.
- Command execution audit log (`~/.honeypot-med/logs/audit.jsonl`).
- Runtime config system (`~/.honeypot-med/config.json`) with engine-mode controls.
- Flexible execution modes: `auto`, `local`, `hybrid`, `remote`.
- Optional remote engine enrichment path (HTTP) with safe local fallback.
- Remote engine controls: auth token, timeout, and retry policy.
- Setup health checks and first-run bootstrap flow for non-developers.
- Distribution-grade packaging scripts for macOS/Linux/Windows.
- Single-command bootstrap installers for macOS/Linux/Windows.
- Packaging CI workflow for cross-platform artifact builds.
- Hosted local `studio` web flow for non-developers.
- Bundled healthcare attack packs (`claims`, `prior-auth`, `triage`, `intake`).
- Share bundle exports now include HTML, JSON, Markdown, SVG social card, and PDF brief.
- Packaged brand artwork generated via `videoagent-image-studio`.

### Changed
- CLI experience now supports plain-English summaries by default in `scan`.
- Demo flow is integrated as a first-class CLI command.
- Reports now include engine metadata for transparency.
- Source selection now supports pasted prompts and bundled packs across scan/share flows.

## 0.2.0 - 2026-04-24

### Added
- HTTP capture service with decoy endpoints (`/capture`, `/decoy/fhir/query`, plugin decoy routes).
- Event schema v1 normalization (`schemas/event-v1.json`).
- JSONL persistence, replay workflow, deterministic fixture and golden report.
- Baseline suppression model with expiry and reason metadata.
- CLI command groups: `analyze`, `capture`, `replay`, `serve`, `purge`.
- Markdown operator report output (`--markdown`).
- Pre-persist redaction policy and retention purge command.
- Ops docs: SLO, alerts, runbook, release checklist.
- One-command demo script (`scripts/demo/run-demo.sh`).

### Changed
- Evidence-first severity policy now default (`proof_required=true`).
- CI now runs advisory replay and blocking gate baseline.

### Validation
- Unit/integration suite expanded to 20 tests and passing.
