#!/usr/bin/env bash
# build-appimage-local.sh — build a local AppImage for developer testing.
#
# Usage:
#   ./scripts/build-appimage-local.sh [VERSION]
#
# VERSION defaults to "dev" if omitted.
# Output: Focus-Mode-App-<VERSION>-x86_64.AppImage in the project root.
#
# appimagetool is downloaded automatically on first run.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

VERSION="${1:-dev}"
APPIMAGE="Focus-Mode-App-${VERSION}-x86_64.AppImage"

echo "==> Building Focus Mode App AppImage v${VERSION}"

# ── Python ──────────────────────────────────────────────────────────────────
# Use the system Python (not one from an active venv) to create a fresh venv.
SYSPY=""
for candidate in /usr/bin/python3 /usr/bin/python python3 python; do
    if "$candidate" -c "import sys; assert sys.version_info >= (3, 9)" 2>/dev/null; then
        SYSPY="$candidate"
        break
    fi
done
if [ -z "$SYSPY" ]; then
    echo "ERROR: Python >= 3.9 not found." >&2
    exit 1
fi
PYVER=$("$SYSPY" --version)
echo "==> Using $SYSPY ($PYVER)"

# ── venv ────────────────────────────────────────────────────────────────────
VENV="${ROOT}/.venv-appimage"

# Recreate the venv if it's broken (e.g. the Python it was built with was removed).
if [ -d "$VENV" ]; then
    if ! "$VENV/bin/python" -c "import sys" 2>/dev/null; then
        echo "==> Detected broken venv — recreating"
        rm -rf "$VENV"
    fi
fi

if [ ! -d "$VENV" ]; then
    echo "==> Creating venv at $VENV"
    "$SYSPY" -m venv "$VENV"
fi

PY="$VENV/bin/python"

echo "==> Installing / updating dependencies"
"$PY" -m pip install --quiet --upgrade pip wheel
# For local builds we don't pin PyInstaller to match CI — we use the latest
# version that supports the system Python.
"$PY" -m pip install --quiet "pyinstaller>=6.11"
"$PY" -m pip install --quiet -r requirements.txt

# Stamp version so importlib.metadata returns the right string at runtime.
sed -i "s/^version = .*/version = \"${VERSION}\"/" pyproject.toml
"$PY" -m pip install --quiet -e .

# ── icon ────────────────────────────────────────────────────────────────────
echo "==> Generating icon"
"$PY" packaging/generate_icon.py

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
for candidate in \
    "$HOME/bin/appimagetool" \
    "$HOME/.local/bin/appimagetool" \
    /usr/local/bin/appimagetool \
    /usr/bin/appimagetool
do
    if [ -x "$candidate" ]; then
        APPIMAGETOOL="$candidate"
        break
    fi
done

if [ -z "$APPIMAGETOOL" ]; then
    APPIMAGETOOL=/tmp/appimagetool-local
    if [ ! -x "$APPIMAGETOOL" ]; then
        echo "==> Downloading appimagetool"
        wget -q \
            "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" \
            -O "$APPIMAGETOOL"
        chmod +x "$APPIMAGETOOL"
    fi
fi

echo "==> Building AppImage"
APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL" AppDir "$APPIMAGE"
chmod +x "$APPIMAGE"

echo ""
echo "Built: ${ROOT}/${APPIMAGE}"
echo "Run:   ./${APPIMAGE}"
