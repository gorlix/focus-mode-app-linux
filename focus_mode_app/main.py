"""
main.py
Main entry point for the Focus Mode application.
Handles initialization, resource loading, and main thread execution.
Integrates session restoration for automatic app recovery.
"""

import logging
import sys
import threading
import signal
from typing import Optional

from focus_mode_app.config import load_config

# Ensure ttkbootstrap's msgcat localization never crashes the app.
# In PyInstaller/AppImage bundles on Ubuntu, Tcl/Tk msgcat module directory structures
# may cause TclError: invalid command name "::msgcat::mcmset".
# We disable localization entirely to bypass the issue, as we do not rely on it.
try:
    import ttkbootstrap.localization

    ttkbootstrap.localization.initialize_localities = bool
except Exception:
    pass
from focus_mode_app.core.storage import load_blocked_items
from focus_mode_app.core.blocker import start_blocking_loop, set_blocking_active
from focus_mode_app.core.session import session_tracker
from focus_mode_app.gui.main_window import AppGui
from focus_mode_app.utils.tray_icon import (
    setup_tray_icon,
    run_qt_with_tkinter,
    stop_tray_icon,
)
from focus_mode_app.api.launcher import start_api, stop_api


_blocking_thread: Optional[threading.Thread] = None
_app_instance: Optional[AppGui] = None


def _setup_logging() -> None:
    """Configure shell logging for HA client and config modules."""
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(logging.WARNING)
    root.addHandler(handler)

    for name in (
        "focus_mode_app.core.ha_client",
        "focus_mode_app.core.ha_config",
        "focus_mode_app.gui.ha_settings_dialog",
        "focus_mode_app.api.launcher",
        "focus_mode_app.api.notifier",
    ):
        lg = logging.getLogger(name)
        lg.setLevel(logging.DEBUG)
        lg.propagate = True


def cleanup_handlers() -> None:
    """Stop all active threads and clean up before exiting."""
    try:
        stop_api()
        set_blocking_active(False)

        try:
            stop_tray_icon()
        except Exception:
            pass

    except Exception:
        pass


def _start_update_check(app_gui: "AppGui") -> None:
    """Fire-and-forget update check — only runs when launched from an AppImage."""
    from focus_mode_app.core.updater import check_for_updates

    def _on_update(new_version: str) -> None:
        try:
            app_gui.after(0, lambda: app_gui.show_update_dialog(new_version))
        except Exception:
            pass

    check_for_updates(_on_update)


def signal_handler(signum: int, frame: Optional[object]) -> None:
    """Handle termination signals to gracefully shut down the app."""
    print("\n[INFO] Termination signal received")
    cleanup_handlers()
    sys.exit(0)


def main() -> None:
    """Initialize and run the Focus Mode App.

    Loads the configuration and persistent data, spawns the background
    blocking thread, sets up the system tray on the main thread, then
    runs the Qt event loop (which drives Tkinter via a QTimer).
    """
    _setup_logging()
    print("[INFO] Starting Focus Mode App...")

    global _blocking_thread, _app_instance

    load_config()
    load_blocked_items()
    session_tracker.load_restore_config()

    _app_instance = AppGui()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # ========================================================================
    # START BLOCKING THREAD
    # ========================================================================

    _blocking_thread = threading.Thread(
        target=start_blocking_loop, daemon=True, name="BlockingThread"
    )
    _blocking_thread.start()
    print("[INFO] Blocking thread started")

    # ========================================================================
    # START API + TRAY ICON (main thread)
    # ========================================================================

    start_api()

    # Qt must run on the main thread. setup_tray_icon() creates the icon;
    # run_qt_with_tkinter() starts exec() and drives Tkinter via QTimer.
    setup_tray_icon(_app_instance)

    # Check for AppImage updates in the background (no-op when not an AppImage).
    _start_update_check(_app_instance)

    # ========================================================================
    # MAIN LOOP (Qt event loop — replaces tk.mainloop())
    # ========================================================================

    try:
        run_qt_with_tkinter(_app_instance)

    except KeyboardInterrupt:
        print("\n[INFO] Keyboard Interrupt received")

    except Exception as e:
        print(f"[ERROR] Main loop error: {e}")

    finally:
        print("[INFO] Closing application...")
        cleanup_handlers()
        sys.exit(0)


if __name__ == "__main__":
    main()
