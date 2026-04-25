#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "[linux] this build script must run on Linux" >&2
  exit 1
fi

VERSION="$(python3 -c 'import sys;sys.path.insert(0,"src");import honeypot_med;print(honeypot_med.__version__)')"
ARCH_RAW="$(uname -m)"
case "$ARCH_RAW" in
  x86_64) ARCH="amd64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *) ARCH="$ARCH_RAW" ;;
esac

DIST_DIR="$ROOT_DIR/dist/linux"
BUILD_DIR="$ROOT_DIR/.release/linux"
VENV_DIR="$ROOT_DIR/.release/.venv-package-linux"

rm -rf "$DIST_DIR" "$BUILD_DIR"
mkdir -p "$DIST_DIR" "$BUILD_DIR/root/usr/local/bin"

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip >/dev/null
pip install pyinstaller >/dev/null

pyinstaller --noconfirm honeypot-med.spec >/dev/null
cp "$ROOT_DIR/dist/honeypot-med" "$BUILD_DIR/root/usr/local/bin/honeypot-med"
chmod +x "$BUILD_DIR/root/usr/local/bin/honeypot-med"

TAR_PATH="$DIST_DIR/honeypot-med-${VERSION}-linux-${ARCH}.tar.gz"
tar -czf "$TAR_PATH" -C "$BUILD_DIR/root" .

echo "[linux] built tarball: $TAR_PATH"

if command -v fpm >/dev/null 2>&1; then
  DEB_PATH="$DIST_DIR/honeypot-med_${VERSION}_${ARCH}.deb"
  RPM_PATH="$DIST_DIR/honeypot-med-${VERSION}-1.${ARCH}.rpm"

  fpm -s dir -t deb -n honeypot-med -v "$VERSION" --architecture "$ARCH" \
    -C "$BUILD_DIR/root" usr/local/bin/honeypot-med >/dev/null
  mv "$ROOT_DIR"/*.deb "$DEB_PATH"

  fpm -s dir -t rpm -n honeypot-med -v "$VERSION" --architecture "$ARCH" \
    -C "$BUILD_DIR/root" usr/local/bin/honeypot-med >/dev/null
  mv "$ROOT_DIR"/*.rpm "$RPM_PATH"

  echo "[linux] built package: $DEB_PATH"
  echo "[linux] built package: $RPM_PATH"
else
  echo "[linux] fpm not found; skipped deb/rpm generation"
fi
