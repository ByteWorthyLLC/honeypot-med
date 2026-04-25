#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "[macos] this build script must run on macOS" >&2
  exit 1
fi

if ! command -v pkgbuild >/dev/null 2>&1; then
  echo "[macos] pkgbuild is required (Xcode command line tools)" >&2
  exit 1
fi

VERSION="$(python3 -c 'import sys;sys.path.insert(0,"src");import honeypot_med;print(honeypot_med.__version__)')"
DIST_DIR="$ROOT_DIR/dist/macos"
BUILD_DIR="$ROOT_DIR/.release/macos"
VENV_DIR="$ROOT_DIR/.release/.venv-package-macos"

rm -rf "$DIST_DIR" "$BUILD_DIR"
mkdir -p "$DIST_DIR" "$BUILD_DIR/root/usr/local/bin"

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip >/dev/null
pip install pyinstaller >/dev/null

pyinstaller --noconfirm honeypot-med.spec >/dev/null
cp "$ROOT_DIR/dist/honeypot-med" "$BUILD_DIR/root/usr/local/bin/honeypot-med"
chmod +x "$BUILD_DIR/root/usr/local/bin/honeypot-med"

PKG_PATH="$DIST_DIR/honeypot-med-${VERSION}-macos.pkg"
pkgbuild \
  --root "$BUILD_DIR/root" \
  --identifier "com.byteworthyllc.honeypotmed" \
  --version "$VERSION" \
  "$PKG_PATH" >/dev/null

TAR_PATH="$DIST_DIR/honeypot-med-${VERSION}-macos.tar.gz"
tar -czf "$TAR_PATH" -C "$BUILD_DIR/root" .

cat <<MSG
[macos] complete
- $PKG_PATH
- $TAR_PATH
MSG
