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
from focus_mode_app.core.storage import load_blocked_items
from focus_mode_app.core.blocker import start_blocking_loop, set_blocking_active
from focus_mode_app.core.session import session_tracker
from focus_mode_app.gui.main_window import AppGui
from focus_mode_app.utils.tray_icon import create_and_run_tray_icon, stop_tray_icon
from focus_mode_app.api.launcher import start_api, stop_api


_blocking_thread: Optional[threading.Thread] = None
_tray_thread: Optional[threading.Thread] = None
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


def signal_handler(signum: int, frame: Optional[object]) -> None:
    """Handle termination signals to gracefully shut down the app."""
    print("\n[INFO] Termination signal received")
    cleanup_handlers()
    sys.exit(0)


def main() -> None:
    """Initialize and run the Focus Mode App.

    Loads the configuration and persistent data, explicitly spawns the
    background blocking thread and the system tray thread, and starts
    the main GUI event loop.
    """
    _setup_logging()
    print("[INFO] Starting Focus Mode App...")

    global _blocking_thread, _tray_thread, _app_instance

    # QApplication must be created in the main thread before any Qt widget
    # (including the tray icon thread). We do it here so TrayThread reuses it.
    try:
        from PyQt6.QtWidgets import QApplication

        if QApplication.instance() is None:
            _qt_app_global = QApplication(sys.argv)  # noqa: F841
    except ImportError:
        pass

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
    # START TRAY ICON THREAD
    # ========================================================================

    _tray_thread = threading.Thread(
        target=create_and_run_tray_icon,
        args=(_app_instance,),
        daemon=True,
        name="TrayThread",
    )
    _tray_thread.start()
    print("[INFO] System tray thread started")

    # ========================================================================
    # GUI MAINLOOP
    # ========================================================================

    start_api()

    try:
        _app_instance.mainloop()

    except KeyboardInterrupt:
        print("\n[INFO] Keyboard Interrupt received")

    except Exception as e:
        print(f"[ERROR] Mainloop error: {e}")

    finally:
        print("[INFO] Closing application...")
        cleanup_handlers()
        sys.exit(0)


if __name__ == "__main__":
    main()
