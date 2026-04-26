# Public Product Surface

Honeypot Med now includes a static site in `site/` that is intended for GitHub Pages.

Goals:

- make the project discoverable outside GitHub search
- expose direct-answer copy for answer engines
- create a cleaner launch surface than a README alone
- give the repo indexable pages for use cases, comparisons, and installers
- publish sanitized evidence examples that visitors can understand before running the tool
- publish generated reports, badges, and integration artifacts that visitors can inspect before installing

Current pages:

- `/`
- `/faq/`
- `/challenge/`
- `/codex/`
- `/field-notes/`
- `/gallery/`
- `/reports/`
- `/reports/healthcare-challenge/`
- `/launch-room/`
- `/integrations/`
- `/contribute/`
- `/media/`
- `/releases/`
- `/use-cases/healthcare-ai/`
- `/use-cases/claims-automation/`
- `/use-cases/prior-authorization/`
- `/use-cases/patient-triage/`
- `/compare/prompt-guardrails-vs-honeypots/`
- `/compare/guardrails-vs-launch-review/`
- `/compare/evals-vs-proof-bundles/`
- `/compare/honeypot-med-vs-generic-red-team-report/`

Discovery artifacts:

- `site/robots.txt`
- `site/sitemap.xml`
- `site/llms.txt`
- `site/site.webmanifest`

Engagement layer:

- zero-key public repo pulse via the GitHub REST API on the Pages surface
- live stars, forks, open-issues, last-push indicators, and latest release hydration
- browser-native reel instead of a hosted video dependency
- sanitized evidence gallery with copy-ready pack commands
- challenge-mode public page with a 10-trap score loop
- specimen codex page with named failure archetypes and offline Trap Lab framing
- field notes page for research questions, unknown ledgers, and local experiments
- generated report gallery with sample badge, SARIF, OTEL, experiment plans, eval-kit adapters, JSON, Markdown, PDF, and social-card outputs
- launch room with copy-ready channel snippets
- integrations page for GitHub Action, SARIF, OpenTelemetry logs, promptfoo, Inspect AI, OpenAI Evals, JSONL, JSON, Markdown, badges, and HTML reports
- contributor quest page for packs, integrations, report templates, and benchmarks
- public installers, bootstrap commands, checksums, and release-manifest links

Deployment:

- GitHub Pages workflow: `.github/workflows/pages.yml`
- Expected public URL: `https://byteworthyllc.github.io/honeypot-med/`

Positioning principle:

The public surface should explain the product in plain English to three audiences at once:

- technical users deciding whether to run it
- non-technical buyers deciding whether it is real
- crawlers and answer engines deciding what it is about
