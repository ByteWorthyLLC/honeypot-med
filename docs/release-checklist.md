# Release Checklist

- [x] Tests pass (`python -m unittest discover -s tests -p 'test_*.py'`)
- [x] Gate baseline passes (`scripts/security/honeypot-gate.sh examples/clean.json`)
- [x] Replay fixture matches golden
- [x] Docs updated (`README`, `docs/*.md`)
- [x] Version bumped in `pyproject.toml` and `__init__.py`
- [x] Changelog/release notes drafted
- [x] Rollback plan validated
- [x] Docker image builds and the studio `/health` endpoint responds
- [x] Release manifest and SHA256 checksum files can be generated
- [x] Default `python app.py` launch path works without API keys
- [x] Launch readiness report passes (`python app.py readiness --strict`)
- [x] Visual proof packet exists in generated sample report (`proof-dossier.html`, `offline-proof.pdf`, `ui-mockup.html`)
