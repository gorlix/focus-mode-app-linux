"""
core/restore.py
Application restoration mechanics without xdotool (Wayland-safe).
"""

import os
import subprocess
import time
from typing import Dict, Tuple, Any, List

from focus_mode_app.core.session import session_tracker


def _clean_env_for_restore() -> dict:
    """Return an environment suitable for restored apps.

    PyInstaller prepends its _internal/ dir to LD_LIBRARY_PATH and saves
    the original value as LD_LIBRARY_PATH_ORIG.  Without this cleanup,
    restored apps inherit Focus Mode's bundled libs and crash immediately.
    AppImage-specific vars (APPDIR, TCL_LIBRARY, …) are stripped for the
    same reason.
    """
    env = os.environ.copy()

    orig_ldpath = env.pop("LD_LIBRARY_PATH_ORIG", None)
    if orig_ldpath is not None:
        if orig_ldpath:
            env["LD_LIBRARY_PATH"] = orig_ldpath
        else:
            env.pop("LD_LIBRARY_PATH", None)

    for var in (
        "APPDIR",
        "APPIMAGE",
        "APPIMAGE_EXTRACT_AND_RUN",
        "TCL_LIBRARY",
        "TK_LIBRARY",
    ):
        env.pop(var, None)

    return env


def restore_app(app_state: Dict[str, Any]) -> Tuple[bool, str]:
    """Restore an application without window positioning.

    Args:
        app_state (Dict[str, Any]): The tracked state dictionary of the killed app.

    Returns:
        Tuple[bool, str]: A tuple containing a boolean success flag and the application name.
    """
    try:
        exe: str | None = app_state.get("exe")
        cmdline: List[str] = app_state.get("cmdline", [])
        cwd: str | None = app_state.get("cwd")
        app_name: str = app_state.get("name", "Unknown")

        if not exe and not cmdline:
            return (False, app_name)

        cmd = cmdline if cmdline else [exe]

        print(f"[INFO] Restoring: {app_name}")

        # Start the process in a new session
        subprocess.Popen(
            cmd,
            cwd=cwd,
            env=_clean_env_for_restore(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        return (True, app_name)

    except Exception as e:
        print(f"[ERROR] Restore {app_state.get('name')}: {e}")
        return (False, app_state.get("name", "Unknown"))


def restore_all_apps() -> int:
    """Restore all applications that were killed during the active session.

    Iterates through the session tracker's queue, restores them, and then clears the session.

    Returns:
        int: The number of applications successfully restored.
    """
    apps = session_tracker.get_killed_apps()

    if not apps:
        print("[INFO] No apps to restore")
        return 0

    print(f"[INFO] Restoring {len(apps)} apps...")

    restored_count = 0
    restored_names = []

    for app_state in apps:
        success, app_name = restore_app(app_state)
        if success:
            restored_count += 1
            restored_names.append(app_name)
            time.sleep(0.3)  # Delay between app restores

    print(f"[INFO] Restored {restored_count}/{len(apps)} apps")

    # Clear the session after restoration attempt
    session_tracker.clear_session()

    return restored_count


__all__ = [
    "restore_app",
    "restore_all_apps",
]
