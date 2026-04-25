#!/usr/bin/env sh
set -eu

mkdir -p "$HOME/.honeypot-med"

command_name="${1:-studio}"

case "$command_name" in
  studio)
    shift || true
    exec honeypot-med studio --host 0.0.0.0 --port "${HONEYPOT_MED_STUDIO_PORT:-8899}" --no-open-browser "$@"
    ;;
  serve)
    shift || true
    exec honeypot-med serve --host 0.0.0.0 --port "${HONEYPOT_MED_CAPTURE_PORT:-8787}" --store "${HONEYPOT_MED_STORE_PATH:-$HOME/.honeypot-med/data/events.jsonl}" "$@"
    ;;
  *)
    exec honeypot-med "$@"
    ;;
esac

