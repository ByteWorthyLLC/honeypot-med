#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/security/honeypot-gate.sh [input.json]

Runs honeypot-med security gate checks.
Defaults to examples/clean.json.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

INPUT_FILE="${1:-examples/clean.json}"

python3 app.py \
  analyze \
  --input "$INPUT_FILE" \
  --gate \
  --max-critical 0 \
  --max-high 0 \
  --max-unproven 0 \
  --pretty

echo "[honeypot-gate] passed"
