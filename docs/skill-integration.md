# Skill Integration

This project is designed to be wrapped by agent skills (Claude/Codex) using only local CLI commands.

## Recommended Skill Actions

- `launch_app`: `python app.py`
- `start_project`: `python app.py start`
- `health_check`: `python app.py doctor --json`
- `show_config`: `python app.py config show --json`
- `quick_scan`: `python app.py scan --input <file>`
- `protect_check`: `python app.py protect --input <file>`
- `full_demo`: `python app.py demo --reports-dir reports`

## Integration Contract

1. Skills should call CLI commands and parse JSON only when `--json` is passed.
2. Skills should prefer `python app.py` or `launch` when the user just wants to use the product.
3. Skills should avoid requiring API keys or cloud credentials for default flows.
4. Skills should preserve exit-code semantics (`10`, `12` as policy failures).
5. Skills should point users to generated markdown/json artifacts for explanations.
6. Skills can set runtime mode once via `config set` for local/hybrid/remote behavior.

## Example Skill Prompt Contract

- "Open the app" -> execute `python app.py`.
- "Run a quick scan" -> execute `scan` and summarize plain output.
- "Why did protect fail?" -> run `protect --json` then explain gate violations.
- "Show me the demo" -> run `demo`, then present report file paths.
