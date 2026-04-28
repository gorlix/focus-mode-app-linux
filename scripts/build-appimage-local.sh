#!/usr/bin/env bash
# build-appimage-local.sh — build a local AppImage for testing (no CI needed).
#
# Usage:
#   ./scripts/build-appimage-local.sh [VERSION]
#
# VERSION defaults to "dev" if omitted.
# Output: Focus-Mode-App-<VERSION>-x86_64.AppImage in the project root.
#
# Requirements (install once):
#   pip install pyinstaller==6.11.0  (inside the venv used below)
#   wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage \
#       -O ~/bin/appimagetool && chmod +x ~/bin/appimagetool

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

VERSION="${1:-dev}"
APPIMAGE="Focus-Mode-App-${VERSION}-x86_64.AppImage"

echo "==> Building Focus Mode App AppImage v${VERSION}"

# ── venv ────────────────────────────────────────────────────────────────────
VENV="${ROOT}/.venv"
if [ ! -f "$VENV/bin/python" ]; then
    echo "==> Creating venv"
    python3 -m venv "$VENV"
fi

echo "==> Installing / updating dependencies"
"$VENV/bin/pip" install --quiet --upgrade pip wheel
"$VENV/bin/pip" install --quiet pyinstaller==6.11.0
"$VENV/bin/pip" install --quiet -r requirements.txt

# Stamp version into pyproject.toml so importlib.metadata returns the right string
sed -i "s/^version = .*/version = \"${VERSION}\"/" pyproject.toml
"$VENV/bin/pip" install --quiet -e .

# ── icon ────────────────────────────────────────────────────────────────────
echo "==> Generating icon"
"$VENV/bin/python" packaging/generate_icon.py

# ── PyInstaller ─────────────────────────────────────────────────────────────
echo "==> Running PyInstaller"
"$VENV/bin/pyinstaller" \
    packaging/focus-mode-app.spec \
    --distpath dist \
    --workpath /tmp/pyinstaller-work \
    --noconfirm

# ── AppDir ──────────────────────────────────────────────────────────────────
echo "==> Assembling AppDir"
rm -rf AppDir
mkdir -p AppDir
cp -r dist/focus-mode-app/. AppDir/
install -m 755 appimage/AppRun                 AppDir/AppRun
install -m 644 appimage/focus-mode-app.desktop AppDir/focus-mode-app.desktop
install -m 644 appimage/focus-mode-app.png     AppDir/focus-mode-app.png
ln -sf focus-mode-app.png AppDir/.DirIcon

# ── appimagetool ────────────────────────────────────────────────────────────
APPIMAGETOOL=""
for candidate in "$HOME/bin/appimagetool" "$HOME/.local/bin/appimagetool" /usr/local/bin/appimagetool; do
    if [ -x "$candidate" ]; then
        APPIMAGETOOL="$candidate"
        break
    fi
done

if [ -z "$APPIMAGETOOL" ]; then
    echo "==> appimagetool not found — downloading to /tmp/appimagetool"
    wget -q \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" \
        -O /tmp/appimagetool
    chmod +x /tmp/appimagetool
    APPIMAGETOOL=/tmp/appimagetool
fi

echo "==> Building AppImage with $APPIMAGETOOL"
APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL" AppDir "$APPIMAGE"
chmod +x "$APPIMAGE"

echo ""
echo "✓  Built: ${ROOT}/${APPIMAGE}"
echo "   Run:   ./${APPIMAGE}"
