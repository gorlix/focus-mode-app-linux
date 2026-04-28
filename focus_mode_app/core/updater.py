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


def apply_update() -> None:
    """Launch appimageupdatetool (or AppImageUpdate) to apply a delta update.

    The tool downloads only the changed blocks and writes the updated AppImage
    in-place.  The user must restart the app after the update completes.
    """
    appimage_path = os.environ.get("APPIMAGE")
    if not appimage_path:
        return

    for tool in ("appimageupdatetool", "AppImageUpdate"):
        try:
            subprocess.Popen(
                [tool, appimage_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            _LOGGER.info("Update launched via %s", tool)
            return
        except FileNotFoundError:
            continue

    _LOGGER.warning(
        "appimageupdatetool not found — install it from "
        "https://github.com/AppImage/AppImageUpdate/releases "
        "to enable one-click updates."
    )


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
