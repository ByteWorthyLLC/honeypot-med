#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

OS="$(uname -s)"
case "$OS" in
  Darwin)
    ./scripts/package/build-macos.sh
    ;;
  Linux)
    ./scripts/package/build-linux.sh
    ;;
  *)
    echo "Unsupported OS for this script: $OS"
    echo "Use scripts/package/build-windows.ps1 on Windows."
    exit 1
    ;;
esac
