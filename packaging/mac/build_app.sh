#!/usr/bin/env bash
# Build a signed macOS application bundle for Deep Organizer using PyInstaller.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
WITH_DMG=false
PYINSTALLER_ARGS=()

for arg in "$@"; do
  if [[ "$arg" == "--with-dmg" ]]; then
    WITH_DMG=true
  else
    PYINSTALLER_ARGS+=("$arg")
  fi
done

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python executable '$PYTHON_BIN' not found. Set PYTHON_BIN to a valid interpreter." >&2
  exit 1
fi

cd "$PROJECT_ROOT"

if ! "$PYTHON_BIN" -m pyinstaller --version >/dev/null 2>&1; then
  echo "Installing PyInstaller into the active environment…"
  "$PYTHON_BIN" -m pip install --upgrade pip wheel
  "$PYTHON_BIN" -m pip install pyinstaller
fi

echo "Building ${PROJECT_ROOT}/dist/Deep Organizer.app"
if ((${#PYINSTALLER_ARGS[@]})); then
  "$PYTHON_BIN" -m PyInstaller "packaging/mac/deep_organizer.spec" --clean --noconfirm "${PYINSTALLER_ARGS[@]}"
else
  "$PYTHON_BIN" -m PyInstaller "packaging/mac/deep_organizer.spec" --clean --noconfirm
fi

echo "App bundle created at: dist/Deep Organizer.app"

if [[ "$WITH_DMG" == true ]]; then
  DMG_PATH="dist/DeepOrganizer.dmg"
  APP_PATH="dist/Deep Organizer.app"
  if [[ ! -d "$APP_PATH" ]]; then
    echo "App bundle not found at $APP_PATH. Skipping DMG creation." >&2
    exit 1
  fi

  echo "Creating compressed DMG at $DMG_PATH"
  rm -f "$DMG_PATH"
  if command -v hdiutil >/dev/null 2>&1; then
    hdiutil create -volname "Deep Organizer" -srcfolder "$APP_PATH" -ov -format UDZO "$DMG_PATH"
  else
    echo "hdiutil not available. Install it or create the DMG manually." >&2
    exit 1
  fi
  echo "DMG written to $DMG_PATH"
fi

cat <<"EON"

Next steps:
  • Sign the app (codesign --deep --force --sign "Developer ID Application: …" "dist/Deep Organizer.app")
  • Notarize with Apple (xcrun notarytool submit …)
  • Distribute the signed/notarized app or DMG.
EON
