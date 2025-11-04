"""
core/restore.py
Ripristino app senza xdotool (Wayland-safe).
"""

import subprocess
import time
from typing import List, Dict, Tuple

from core.session import session_tracker


def restore_app(app_state: Dict) -> Tuple[bool, str]:
    """
    Ripristina app senza window positioning.

    Returns:
        (success: bool, app_name: str)
    """
    try:
        exe = app_state.get('exe')
        cmdline = app_state.get('cmdline', [])
        cwd = app_state.get('cwd')
        app_name = app_state.get('name')

        if not exe and not cmdline:
            return (False, app_name)

        cmd = cmdline if cmdline else [exe]

        print(f"[INFO] Restoring: {app_name}")

        # Avvia processo
        subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        return (True, app_name)

    except Exception as e:
        print(f"[ERROR] Restore {app_state.get('name')}: {e}")
        return (False, app_state.get('name', 'Unknown'))


def restore_all_apps() -> int:
    """
    Ripristina tutte le app killate.

    Returns:
        Numero app ripristinate con successo
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
            time.sleep(0.3)  # Delay tra app

    print(f"[INFO] Restored {restored_count}/{len(apps)} apps")

    # Pulisci sessione
    session_tracker.clear_session()

    return restored_count


__all__ = [
    'restore_app',
    'restore_all_apps',
]
