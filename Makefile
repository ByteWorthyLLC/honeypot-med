PYTHON ?= python3

.PHONY: run start doctor config scan protect analyze replay serve capture purge gate demo share packs studio launch package package-linux package-macos package-windows bootstrap-linux-macos bootstrap-windows release-manifest docker-build docker-studio docker-capture test lint

run:
	./run.sh

start:
	$(PYTHON) app.py start --download-assets

doctor:
	$(PYTHON) app.py doctor

config:
	$(PYTHON) app.py config show --json

analyze:
	$(PYTHON) app.py analyze --input examples/sample.json --pretty

scan:
	$(PYTHON) app.py scan --input examples/sample.json

protect:
	$(PYTHON) app.py protect --input examples/clean.json

replay:
	$(PYTHON) app.py replay --store data/events.jsonl --pretty

serve:
	$(PYTHON) app.py serve --store data/events.jsonl

capture:
	$(PYTHON) app.py capture --input examples/sample.json --store data/events.jsonl --pretty

purge:
	$(PYTHON) app.py purge --store data/events.jsonl --days 30 --pretty

gate:
	scripts/security/honeypot-gate.sh examples/clean.json

demo:
	$(PYTHON) app.py demo --reports-dir reports --pretty

share:
	$(PYTHON) app.py share --pack claims --outdir reports/share

packs:
	$(PYTHON) app.py packs

studio:
	$(PYTHON) app.py studio

launch:
	$(PYTHON) app.py launch

package:
	./scripts/package/build-release.sh

release-manifest:
	$(PYTHON) scripts/release/generate-manifest.py

package-linux:
	./scripts/package/build-linux.sh

package-macos:
	./scripts/package/build-macos.sh

package-windows:
	pwsh -File scripts/package/build-windows.ps1

bootstrap-linux-macos:
	./scripts/bootstrap/install.sh latest

bootstrap-windows:
	pwsh -File scripts/bootstrap/install.ps1 -Version latest

docker-build:
	docker build -t honeypot-med:local .

docker-studio:
	docker compose up --build studio

docker-capture:
	docker compose up --build capture

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'

lint:
	$(PYTHON) -m py_compile app.py src/honeypot_med/*.py
