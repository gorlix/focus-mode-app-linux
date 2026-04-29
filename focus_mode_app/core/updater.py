"""
core/updater.py
Checks for newer AppImage releases on GitHub via the Releases API.
Only active when the app is running inside an AppImage (APPIMAGE env var set).
"""

import logging
import os
import subprocess
import threading
from typing import Callable, Optional

_LOGGER = logging.getLogger(__name__)

_GITHUB_API = "https://api.github.com/repos/gorlix/focus-mode-app-linux/releases/latest"


def is_running_as_appimage() -> bool:
    """Return True when the process was launched from an AppImage."""
    return bool(os.environ.get("APPIMAGE"))


def get_current_version() -> Optional[str]:
    """Return the installed package version string, or None on failure."""
    try:
        from importlib.metadata import version

        return version("focus-mode-app")
    except Exception:
        return None


def check_for_updates(callback: Callable[[str], None]) -> None:
    """Start a daemon thread that checks GitHub for a newer release.

    Args:
        callback: Called with the new version string (e.g. "2.1.0") when
                  a newer release is found.  Called from the daemon thread —
                  use tk.after() or similar to update the GUI safely.
    """
    if not is_running_as_appimage():
        return
    threading.Thread(
        target=_check_github,
        args=(callback,),
        daemon=True,
        name="UpdateChecker",
    ).start()


def _find_update_tool() -> Optional[str]:
    """Return path to appimageupdatetool, preferring the bundled copy in $APPDIR."""
    import shutil

    appdir = os.environ.get("APPDIR", "")
    if appdir:
        candidate = os.path.join(appdir, "appimageupdatetool")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return shutil.which("appimageupdatetool")


def apply_update() -> bool:
    """Launch appimageupdatetool to perform a delta update in-place.

    Returns True if the tool was launched successfully, False if not found.
    Uses APPIMAGE_EXTRACT_AND_RUN=1 so the tool (itself an AppImage) works
    without FUSE.  The process is detached — the user must restart the app.
    """
    appimage_path = os.environ.get("APPIMAGE")
    if not appimage_path:
        _LOGGER.debug("Not running as AppImage — skipping update")
        return False

    tool = _find_update_tool()
    if not tool:
        _LOGGER.warning(
            "appimageupdatetool not found — install it from "
            "https://github.com/AppImage/AppImageUpdate/releases"
        )
        return False

    env = os.environ.copy()
    env["APPIMAGE_EXTRACT_AND_RUN"] = "1"

    try:
        subprocess.Popen(
            [tool, appimage_path],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        _LOGGER.info("Update launched via %s", tool)
        return True
    except Exception as e:
        _LOGGER.error("Failed to launch update tool: %s", e)
        return False


# ============================================================================
# INTERNAL
# ============================================================================


def _check_github(callback: Callable[[str], None]) -> None:
    try:
        import requests

        resp = requests.get(
            _GITHUB_API,
            timeout=10,
            headers={"Accept": "application/vnd.github+json"},
        )
        if resp.status_code != 200:
            _LOGGER.debug("GitHub API returned %s", resp.status_code)
            return

        latest_tag: str = resp.json().get("tag_name", "")
        latest_version = latest_tag.lstrip("v")
        current_version = get_current_version()

        if not latest_version or not current_version:
            return

        if _is_newer(latest_version, current_version):
            _LOGGER.info("Update available: %s → %s", current_version, latest_version)
            callback(latest_version)
        else:
            _LOGGER.debug("Already up to date (%s)", current_version)

    except Exception as e:
        _LOGGER.debug("Update check failed: %s", e)


def _is_newer(latest: str, current: str) -> bool:
    """Return True if latest is strictly greater than current (semver tuples)."""

    def _parts(v: str) -> tuple:
        try:
            return tuple(int(x) for x in v.split("."))
        except ValueError:
            return (0,)

    return _parts(latest) > _parts(current)
