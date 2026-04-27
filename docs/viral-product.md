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

6. Challenge-loop
`honeypot-med challenge` asks "Can your healthcare AI survive 10 traps?", then outputs a score, badge, generated report, baseline comparison, SARIF, OTEL logs, JSON, Markdown, PDF, and social card.

7. CI-loop
The root GitHub Action lets another repo run the challenge and publish artifacts without writing custom glue code.

8. Trap-lab loop
The project names failure modes as specimens so generated reports feel like field guides instead of compliance PDFs.

9. Inquiry-loop
`honeypot-med inquire` produces research questions, unknown ledgers, and local experiment prompts so curiosity can outrank promotion.

10. Experiment-loop
`honeypot-med experiment` turns one report into counterfactual prompt decks, ablation ladders, experiment matrices, and a question atlas.

11. Eval-kit loop
`honeypot-med eval-kit` exports canonical JSONL plus promptfoo, Inspect AI, and legacy OpenAI Evals adapter files so teams can reuse the traps in their existing eval stack.

12. Casebook-loop
`honeypot-med casebook` turns one run into a redacted forensic notebook, traparium museum, unknowns page, failure recipes, trap tree, and notebook.

13. Daily-loop
`honeypot-med daily` creates a deterministic seeded dungeon so the same local challenge can be replayed and shared without hosted infrastructure.

14. Prompt-CTF loop
`honeypot-med ctf` turns evidence into flags that are predicates, not secrets: data exfiltration, safeguard bypass, authority costume, unsafe tool reach, and falsifiable unknowns.

15. HF-Lab loop
`honeypot-med hf-mirror plan` and eval-kit Hugging Face cards make the project easy to fold into public dataset/model-card workflows without default downloads or API calls.

16. Diff-loop
`honeypot-med casebook-diff` makes two runs comparable as evidence shifts instead of social proof.

17. Release-loop
`honeypot-med release-kit` packages generated report directories into zip files with checksums and release notes.

18. Visual-packet loop
Every run now surfaces a proof dossier, offline proof PDF, and generated UI mockup so the artifact is immediately legible to non-terminal audiences.

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
9. Public evidence gallery with sanitized verdict examples
10. Added appeals, eligibility, and utilization management attack packs
11. Challenge mode with default 10-trap healthcare AI pack
12. README badge output for score sharing
13. SARIF and OpenTelemetry log exports
14. Root GitHub Action metadata for CI use
15. Launch Room with copy-ready Product Hunt, Show HN, X, LinkedIn, Reddit, newsletter, and release copy
16. Generated public report gallery
17. Contributor quest surface for packs, integrations, report templates, and benchmarks
18. Specimen Codex and offline Trap Lab artifacts
19. `honeypot-med lab` command for codex, field guide, trap ledger, visual proof dossier, offline proof PDF, UI mockup, and text proof generation
20. Field Notes page and `honeypot-med inquire` command for curiosity-first artifacts
21. `honeypot-med experiment` command for counterfactuals, ablations, question atlas, and experiment plans
22. `honeypot-med eval-kit` command for promptfoo, Inspect AI, OpenAI Evals, and canonical JSONL adapters
23. `honeypot-med casebook` command and bundled casebook artifacts in challenge/share output
24. `honeypot-med daily` deterministic daily dungeon with seed, score JSON, and SVG map
25. `honeypot-med ctf` prompt CTF with evidence-predicate flags, hints, writeup, and score JSON
26. JUnit XML and GitHub step-summary exports for CI hygiene
27. OpenInference and LangSmith JSONL exports plus OTEL collector fixture
28. Hugging Face-ready dataset card, system card, artifact manifest, and `hf-mirror` plan/transform workflow
29. PNG social-card and badge outputs for non-SVG surfaces
30. `honeypot-med casebook-diff` for local evidence-shift review
31. `honeypot-med release-kit` for release-ready zipped report bundles with checksums
32. Visual proof dossier, offline proof PDF, and generated UI mockup surfaced in Studio, share pages, docs, and public site copy

## What To Prioritize Next

1. Publish generated challenge bundles as downloadable artifacts in releases.
2. Add hosted deployment templates for Fly.io, Railway, and Render instead of Docker-only self-hosting.
3. Add more adapter inputs for LangChain traces, promptfoo outputs, Inspect AI logs, and plain HTTP agent targets.
4. Add release-page automation that attaches local bundles to GitHub Releases.
