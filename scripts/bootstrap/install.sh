#!/usr/bin/env bash
set -euo pipefail

REPO="${HONEYPOT_MED_REPO:-ByteWorthyLLC/honeypot-med}"
VERSION="${1:-latest}"
INSTALL_DIR="${HONEYPOT_MED_INSTALL_DIR:-$HOME/.local/bin}"

OS="$(uname -s)"
ARCH_RAW="$(uname -m)"
case "$ARCH_RAW" in
  x86_64) ARCH="amd64" ;;
  arm64|aarch64) ARCH="arm64" ;;
  *) ARCH="$ARCH_RAW" ;;
esac

if [[ "$VERSION" == "latest" ]]; then
  TAG="latest"
  RESOLVED_TAG="$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" | python3 -c 'import json,sys;print(json.load(sys.stdin)["tag_name"])')"
  ASSET_VERSION="${RESOLVED_TAG#v}"
else
  TAG="tags/$VERSION"
  ASSET_VERSION="${VERSION#v}"
fi

BASE_URL="https://github.com/$REPO/releases/$TAG/download"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

mkdir -p "$INSTALL_DIR"

if [[ "$OS" == "Darwin" ]]; then
  ASSET="honeypot-med-${ASSET_VERSION}-macos.pkg"
  URL="$BASE_URL/$ASSET"
  FILE="$TMP_DIR/$ASSET"
  echo "[bootstrap] downloading $URL"
  curl -fsSL "$URL" -o "$FILE"
  echo "[bootstrap] installing macOS package"
  sudo installer -pkg "$FILE" -target /
  echo "[bootstrap] installed. Run: honeypot-med"
  exit 0
fi

if [[ "$OS" == "Linux" ]]; then
  ASSET="honeypot-med-${ASSET_VERSION}-linux-${ARCH}.tar.gz"
  URL="$BASE_URL/$ASSET"
  FILE="$TMP_DIR/$ASSET"
  echo "[bootstrap] downloading $URL"
  curl -fsSL "$URL" -o "$FILE"

  EXTRACT_DIR="$TMP_DIR/extract"
  mkdir -p "$EXTRACT_DIR"
  tar -xzf "$FILE" -C "$EXTRACT_DIR"

  if [[ -f "$EXTRACT_DIR/usr/local/bin/honeypot-med" ]]; then
    cp "$EXTRACT_DIR/usr/local/bin/honeypot-med" "$INSTALL_DIR/honeypot-med"
  elif [[ -f "$EXTRACT_DIR/honeypot-med" ]]; then
    cp "$EXTRACT_DIR/honeypot-med" "$INSTALL_DIR/honeypot-med"
  else
    echo "[bootstrap] no honeypot-med binary found in archive" >&2
    exit 1
  fi

  chmod +x "$INSTALL_DIR/honeypot-med"
  echo "[bootstrap] installed to $INSTALL_DIR/honeypot-med"
  echo "[bootstrap] ensure $INSTALL_DIR is on PATH"
  echo "[bootstrap] run: honeypot-med"
  exit 0
fi

echo "Unsupported OS: $OS" >&2
exit 1
