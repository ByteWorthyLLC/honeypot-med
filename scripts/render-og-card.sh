#!/usr/bin/env bash
# Render site/assets/og-card.svg → site/assets/og-card.png (1200x630)
# Requirements (in priority order):
#   1. rsvg-convert  (brew install librsvg)
#   2. inkscape      (brew install inkscape)
#   3. playwright + chromium (npm install -g playwright && npx playwright install chromium)
#
# This script uses whichever is available.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SVG="$REPO_ROOT/site/assets/og-card.svg"
PNG="$REPO_ROOT/site/assets/og-card.png"

if command -v rsvg-convert &>/dev/null; then
  echo "→ rsvg-convert"
  rsvg-convert -w 1200 -h 630 "$SVG" -o "$PNG"

elif command -v inkscape &>/dev/null; then
  echo "→ inkscape"
  inkscape -w 1200 -h 630 --export-type=png --export-filename="$PNG" "$SVG"

else
  echo "→ playwright/chromium"
  # Find a chromium executable in the playwright cache
  CHROME=$(find "$HOME/Library/Caches/ms-playwright" -name "Google Chrome for Testing" -type f 2>/dev/null | head -1)
  if [ -z "$CHROME" ]; then
    echo "ERROR: no rsvg-convert, inkscape, or playwright chromium found." >&2
    echo "Install one: brew install librsvg  OR  brew install inkscape" >&2
    exit 1
  fi
  node - <<JS
const { chromium } = require('/opt/homebrew/lib/node_modules/playwright');
(async () => {
  const browser = await chromium.launch({ executablePath: '${CHROME}' });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1200, height: 630 });
  await page.goto('file://${SVG}', { waitUntil: 'networkidle' });
  await page.screenshot({ path: '${PNG}', clip: { x:0, y:0, width:1200, height:630 } });
  await browser.close();
})();
JS
fi

echo "✓ $PNG"
file "$PNG"
