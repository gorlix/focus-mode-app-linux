"""
utils/tray_icon.py
System tray icon usando PyQt6 - Versione funzionante finale.
"""

import sys
import atexit

try:
    from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
    from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
    from PyQt6.QtCore import Qt, QTimer
except ImportError:
    print("[ERROR] PyQt6 non installato: pip install PyQt6")
    sys.exit(1)

from config import TRAY_ID, TRAY_TOOLTIP
from core.blocker import is_blocking_active, toggle_blocking
from core.storage import save_blocked_items

# Riferimenti globali
_tray_icon = None
_app_gui = None
_qt_app = None
_is_quitting = False


# ============================================================================
# CREAZIONE ICONA
# ============================================================================

def create_tray_icon_pixmap():
    """Crea un QPixmap per l'icona tray."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Cerchio viola Material 3
    painter.setBrush(QColor("#6750A4"))
    painter.setPen(QColor("white"))
    painter.drawEllipse(4, 4, 56, 56)

    # Lettera M
    painter.setPen(QColor("white"))
    font = QFont("Sans", 28, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "M")

    painter.end()

    return pixmap


# ============================================================================
# GESTIONE MENU
# ============================================================================

def get_toggle_text():
    """Testo dinamico per toggle."""
    return "⏸️ Ferma Blocco" if is_blocking_active() else "▶️ Avvia Blocco"


def create_tray_menu():
    """Crea il menu contestuale."""
    menu = QMenu()

    toggle_action = menu.addAction(get_toggle_text())
    toggle_action.triggered.connect(on_toggle_blocking)

    menu.addSeparator()

    show_action = menu.addAction("👁️ Mostra GUI")
    show_action.triggered.connect(on_show_gui)

    quit_action = menu.addAction("🚪 Esci")
    quit_action.triggered.connect(on_quit_app)

    return menu


def update_menu():
    """Aggiorna il menu."""
    if _tray_icon and not _is_quitting:
        try:
            menu = create_tray_menu()
            _tray_icon.setContextMenu(menu)
        except:
            pass


# ============================================================================
# CALLBACK
# ============================================================================

def on_toggle_blocking():
    """Toggle blocco."""
    if _is_quitting:
        return

    try:
        new_state = toggle_blocking()
        print(f"[INFO] Blocco {'ATTIVATO' if new_state else 'DISATTIVATO'}")

        update_menu()

        if _app_gui and hasattr(_app_gui, 'update_toggle_button'):
            try:
                _app_gui.after(0, _app_gui.update_toggle_button)
            except:
                pass
    except Exception as e:
        print(f"[ERROR] Toggle: {e}")


def on_show_gui():
    """Mostra GUI."""
    if _is_quitting or not _app_gui:
        return

    try:
        _app_gui.after(0, lambda: [
            _app_gui.deiconify(),
            _app_gui.lift(),
            _app_gui.focus_force()
        ])
        print("[DEBUG] GUI mostrata")
    except Exception as e:
        print(f"[ERROR] Mostra GUI: {e}")


def on_quit_app():
    """Chiude applicazione."""
    global _is_quitting

    if _is_quitting:
        return

    _is_quitting = True
    print("[INFO] Uscita richiesta")

    try:
        save_blocked_items()
    except:
        pass

    # Stop Qt
    if _qt_app:
        try:
            _qt_app.quit()
        except:
            pass

    # Stop Tkinter
    if _app_gui:
        try:
            _app_gui.after(0, _app_gui.quit)
        except:
            pass


def on_tray_activated(reason):
    """Gestisce click icona."""
    if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
        on_show_gui()


# ============================================================================
# CLEANUP HANDLER
# ============================================================================

def cleanup_qt():
    """Cleanup per evitare crash."""
    global _is_quitting

    _is_quitting = True

    if _tray_icon:
        try:
            _tray_icon.hide()
        except:
            pass

    if _qt_app:
        try:
            _qt_app.quit()
        except:
            pass


# Registra cleanup
atexit.register(cleanup_qt)


# ============================================================================
# SETUP E AVVIO
# ============================================================================

def create_and_run_tray_icon(app_gui=None):
    """
    Crea e avvia system tray icon.
    BLOCCANTE - deve girare in thread separato.
    """
    global _tray_icon, _app_gui, _qt_app

    try:
        _app_gui = app_gui

        # Crea QApplication
        _qt_app = QApplication.instance()
        if _qt_app is None:
            _qt_app = QApplication(sys.argv)

        # Crea icona
        pixmap = create_tray_icon_pixmap()
        icon = QIcon(pixmap)

        _tray_icon = QSystemTrayIcon(icon)
        _tray_icon.setToolTip(TRAY_TOOLTIP)

        # Menu
        menu = create_tray_menu()
        _tray_icon.setContextMenu(menu)

        # Click handler
        _tray_icon.activated.connect(on_tray_activated)

        # Mostra icona
        _tray_icon.show()

        print(f"[INFO] System tray icon creata")
        print("[INFO] Click destro = Menu | Doppio click = GUI")

        # Timer per aggiornamenti
        timer = QTimer()
        timer.timeout.connect(lambda: None)
        timer.start(100)

        # Avvia Qt event loop (BLOCCANTE)
        sys.exit(_qt_app.exec())

    except Exception as e:
        print(f"[ERROR] Tray icon: {e}")
        import traceback
        traceback.print_exc()


def update_tray_menu():
    """Aggiorna menu."""
    update_menu()


def stop_tray_icon():
    """Ferma tray icon."""
    cleanup_qt()


def get_tray_icon():
    """Ritorna tray icon."""
    return _tray_icon


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    'create_and_run_tray_icon',
    'update_tray_menu',
    'stop_tray_icon',
    'get_tray_icon',
]
