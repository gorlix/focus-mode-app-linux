"""
utils/tray_icon.py
System tray icon using PyQt6.
Handles background minimization and app controls.
"""

import sys
import atexit

try:
    from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
    from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
    from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal
except ImportError:
    print("[ERROR] PyQt6 not installed: pip install PyQt6")
    sys.exit(1)

from focus_mode_app.config import TRAY_TOOLTIP
from focus_mode_app.core.blocker import is_blocking_active, toggle_blocking
from focus_mode_app.core.storage import save_blocked_items

# Global references
_tray_icon = None
_app_gui = None
_qt_app = None
_is_quitting = False
_controller = None


class TrayController(QObject):
    """Qt signal dispatcher for thread-safe tray icon updates."""

    update_menu_signal = pyqtSignal()
    hide_signal = pyqtSignal()
    quit_signal = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.update_menu_signal.connect(self.do_update_menu)
        self.hide_signal.connect(self.do_hide)
        self.quit_signal.connect(self.do_quit)

    def do_update_menu(self) -> None:
        if _tray_icon and not _is_quitting:
            try:
                menu = create_tray_menu()
                _tray_icon.setContextMenu(menu)
            except Exception:
                pass

    def do_hide(self) -> None:
        if _tray_icon:
            try:
                _tray_icon.hide()
            except Exception:
                pass

    def do_quit(self) -> None:
        if _qt_app:
            try:
                _qt_app.quit()
            except Exception:
                pass


# ============================================================================
# ICON CREATION
# ============================================================================


def create_tray_icon_pixmap() -> QPixmap:
    """Create a QPixmap for the tray icon."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Material 3 purple circle
    painter.setBrush(QColor("#6750A4"))
    painter.setPen(QColor("white"))
    painter.drawEllipse(4, 4, 56, 56)

    # Letter M
    painter.setPen(QColor("white"))
    font = QFont("Sans", 28, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "M")

    painter.end()

    return pixmap


# ============================================================================
# MENU MANAGEMENT
# ============================================================================


def get_toggle_text() -> str:
    """Return dynamic text for the toggle action."""
    return "⏸️ Stop Block" if is_blocking_active() else "▶️ Start Block"


def create_tray_menu() -> QMenu:
    """Create the contextual tray menu."""
    menu = QMenu()

    toggle_action = menu.addAction(get_toggle_text())
    toggle_action.triggered.connect(on_toggle_blocking)

    menu.addSeparator()

    show_action = menu.addAction("👁️ Show GUI")
    show_action.triggered.connect(on_show_gui)

    quit_action = menu.addAction("🚪 Quit")
    quit_action.triggered.connect(on_quit_app)

    return menu


def update_menu() -> None:
    """Update the context menu via signal for cross-thread safety."""
    global _controller
    if _controller and not _is_quitting:
        try:
            _controller.update_menu_signal.emit()
        except Exception as e:
            print(f"[ERROR] update_menu signal emit failed: {e}")


# ============================================================================
# CALLBACKS
# ============================================================================


def on_toggle_blocking() -> None:
    """Toggle blocking state via the tray menu."""
    if _is_quitting:
        return

    try:
        new_state = toggle_blocking()
        print(f"[INFO] Block {'ACTIVATED' if new_state else 'DEACTIVATED'}")

        update_menu()

        if _app_gui and hasattr(_app_gui, "update_toggle_button"):
            try:
                _app_gui.after(0, _app_gui.update_toggle_button)
            except Exception:
                pass
    except Exception as e:
        print(f"[ERROR] Toggle: {e}")


def on_show_gui() -> None:
    """Show the graphical user interface."""
    if _is_quitting or not _app_gui:
        return

    try:
        _app_gui.after(
            0, lambda: [_app_gui.deiconify(), _app_gui.lift(), _app_gui.focus_force()]
        )
        print("[DEBUG] GUI shown")
    except Exception as e:
        print(f"[ERROR] Show GUI: {e}")


def on_quit_app() -> None:
    """Close the application permanently."""
    global _is_quitting

    if _is_quitting:
        return

    _is_quitting = True
    print("[INFO] Exit requested")

    try:
        save_blocked_items()
    except Exception:
        pass

    # Stop Qt
    if _qt_app:
        try:
            _qt_app.quit()
        except Exception:
            pass

    # Stop Tkinter
    if _app_gui:
        try:
            _app_gui.after(0, _app_gui.quit)
        except Exception:
            pass


def on_tray_activated(reason: QSystemTrayIcon.ActivationReason) -> None:
    """Handle tray icon clicks."""
    if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
        on_show_gui()


# ============================================================================
# CLEANUP HANDLER
# ============================================================================


def cleanup_qt() -> None:
    """Clean up Qt resources via signals to avoid cross-thread crashes."""
    global _is_quitting, _controller

    _is_quitting = True

    if _controller:
        try:
            _controller.hide_signal.emit()
            _controller.quit_signal.emit()
        except Exception:
            pass


# Register cleanup
atexit.register(cleanup_qt)


# ============================================================================
# SETUP AND LAUNCH
# ============================================================================


def create_and_run_tray_icon(app_gui=None) -> None:
    """Create and start the system tray icon loop.

    BLOCKING CALL — must run in a separate thread.
    """
    global _tray_icon, _app_gui, _qt_app, _controller

    try:
        _app_gui = app_gui

        # Reuse QApplication created in main thread if available
        _qt_app = QApplication.instance()
        if _qt_app is None:
            _qt_app = QApplication(sys.argv)

        _controller = TrayController()

        # Create icon
        pixmap = create_tray_icon_pixmap()
        icon = QIcon(pixmap)

        _tray_icon = QSystemTrayIcon(icon)
        _tray_icon.setToolTip(TRAY_TOOLTIP)

        # Menu
        menu = create_tray_menu()
        _tray_icon.setContextMenu(menu)

        # Click handler
        _tray_icon.activated.connect(on_tray_activated)

        # Show icon
        _tray_icon.show()

        print("[INFO] System tray icon created")
        print("[INFO] Right click = Menu | Double click = GUI")

        # Keepalive timer — prevents Qt event loop from blocking indefinitely
        timer = QTimer()
        timer.timeout.connect(lambda: None)
        timer.start(100)

        # Start Qt event loop (BLOCKING)
        sys.exit(_qt_app.exec())

    except Exception as e:
        print(f"[ERROR] Tray icon: {e}")
        import traceback

        traceback.print_exc()


def update_tray_menu() -> None:
    """Update the tray context menu."""
    update_menu()


def stop_tray_icon() -> None:
    """Stop the tray icon and perform cleanup."""
    cleanup_qt()


def get_tray_icon() -> QSystemTrayIcon:
    """Return the active Qt tray icon object."""
    return _tray_icon


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "create_and_run_tray_icon",
    "update_tray_menu",
    "stop_tray_icon",
    "get_tray_icon",
]
