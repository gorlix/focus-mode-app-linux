"""
utils/tray_icon.py
System tray icon using PyQt6.

Architecture: Qt event loop runs on the MAIN thread. Tkinter is driven
by a QTimer calling tk_root.update() every 16 ms — this replaces the
traditional tk.mainloop() call. The tray thread is no longer used.
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

# Global references (all live on the main thread)
_tray_icon = None
_app_gui = None
_qt_app = None
_tk_timer = None
_is_quitting = False
_controller = None


class TrayController(QObject):
    """Qt signal dispatcher — allows other threads to safely update the tray."""

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
                _tray_icon.setContextMenu(create_tray_menu())
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

    painter.setBrush(QColor("#6750A4"))
    painter.setPen(QColor("white"))
    painter.drawEllipse(4, 4, 56, 56)

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
    """Update the tray menu — safe to call from any thread via signal."""
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
    global _is_quitting
    if _is_quitting:
        return
    _is_quitting = True
    print("[INFO] Exit requested")

    try:
        save_blocked_items()
    except Exception:
        pass

    # Quit Qt event loop — run_qt_with_tkinter() will then return
    if _qt_app:
        try:
            _qt_app.quit()
        except Exception:
            pass


def on_tray_activated(reason: QSystemTrayIcon.ActivationReason) -> None:
    if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
        on_show_gui()


# ============================================================================
# CLEANUP
# ============================================================================


def cleanup_qt() -> None:
    """Hide tray icon and stop Qt event loop. Safe to call from any thread."""
    global _is_quitting, _controller

    _is_quitting = True

    if _controller:
        try:
            _controller.hide_signal.emit()
            _controller.quit_signal.emit()
        except Exception:
            pass


atexit.register(cleanup_qt)


# ============================================================================
# MAIN-THREAD SETUP AND LAUNCH
# ============================================================================


def setup_tray_icon(app_gui=None) -> None:
    """Create and show the system tray icon.

    Must be called from the MAIN thread, before run_qt_with_tkinter().
    Does NOT start the Qt event loop.
    """
    global _tray_icon, _app_gui, _qt_app, _controller

    _app_gui = app_gui

    _qt_app = QApplication.instance()
    if _qt_app is None:
        _qt_app = QApplication(sys.argv)

    _controller = TrayController()

    pixmap = create_tray_icon_pixmap()
    _tray_icon = QSystemTrayIcon(QIcon(pixmap))
    _tray_icon.setToolTip(TRAY_TOOLTIP)
    _tray_icon.setContextMenu(create_tray_menu())
    _tray_icon.activated.connect(on_tray_activated)
    _tray_icon.show()

    print("[INFO] System tray icon created")
    print("[INFO] Right click = Menu | Double click = GUI")


def run_qt_with_tkinter(tk_root) -> int:
    """Run the Qt event loop on the main thread, driving Tkinter via QTimer.

    Replaces tk_root.mainloop(). BLOCKING — returns when the app quits.
    """
    global _tk_timer

    if _qt_app is None:
        return 1

    def _tick() -> None:
        if _is_quitting:
            return
        try:
            tk_root.update()
        except Exception:
            # Tkinter window destroyed — shut down Qt too
            if _qt_app and not _is_quitting:
                _qt_app.quit()

    _tk_timer = QTimer()
    _tk_timer.timeout.connect(_tick)
    _tk_timer.start(16)  # ~60 fps

    print("[INFO] Qt event loop started on main thread")
    return _qt_app.exec()


# ============================================================================
# PUBLIC API
# ============================================================================


def update_tray_menu() -> None:
    """Refresh the tray context menu (safe from any thread)."""
    update_menu()


def stop_tray_icon() -> None:
    """Stop the tray icon and request Qt shutdown."""
    cleanup_qt()


def get_tray_icon() -> QSystemTrayIcon:
    """Return the active Qt tray icon object."""
    return _tray_icon


__all__ = [
    "setup_tray_icon",
    "run_qt_with_tkinter",
    "update_tray_menu",
    "stop_tray_icon",
    "get_tray_icon",
]
