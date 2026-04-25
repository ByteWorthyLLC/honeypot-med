# Public Product Surface

Honeypot Med now includes a static site in `site/` that is intended for GitHub Pages.

Goals:

- make the project discoverable outside GitHub search
- expose direct-answer copy for answer engines
- create a cleaner launch surface than a README alone
- give the repo indexable pages for use cases, comparisons, and installers

Current pages:

- `/`
- `/faq/`
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
- public installers, bootstrap commands, checksums, and release-manifest links

Deployment:

- GitHub Pages workflow: `.github/workflows/pages.yml`
- Expected public URL: `https://byteworthyllc.github.io/honeypot-med/`

Positioning principle:

The public surface should explain the product in plain English to three audiences at once:

- technical users deciding whether to run it
- non-technical buyers deciding whether it is real
- crawlers and answer engines deciding what it is about
