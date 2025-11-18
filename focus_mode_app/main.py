"""
main.py
Entry point principale dell'applicazione Focus Mode App.
Gestisce inizializzazione, caricamento risorse e avvio thread principali.
Integra session restore per il ripristino app automatico.
"""

import sys
import threading
import os
import signal

from focus_mode_app.config import load_config
from focus_mode_app.core.storage import load_blocked_items
from focus_mode_app.core.blocker import start_blocking_loop, set_blocking_active
from focus_mode_app.core.session import session_tracker
from focus_mode_app.gui.main_window import AppGui
from focus_mode_app.utils.tray_icon import create_and_run_tray_icon, stop_tray_icon


_blocking_thread = None
_tray_thread = None
_app_instance = None


def cleanup_handlers():
    """Ferma i thread prima di uscire."""
    try:
        set_blocking_active(False)

        try:
            stop_tray_icon()
        except:
            pass

    except:
        pass


def signal_handler(signum, frame):
    """Gestisce segnali di interruzione."""
    print("\n[INFO] Segnale di interruzione ricevuto")
    cleanup_handlers()
    sys.exit(0)


def main():
    """
    Funzione principale che avvia l'applicazione Focus Mode App.
    Inizializza configurazione, carica dati persistenti, avvia GUI e thread worker.
    """
    print("[INFO] Avvio Focus Mode App...")

    global _blocking_thread, _tray_thread, _app_instance

    load_config()

    load_blocked_items()

    session_tracker.load_restore_config()

    _app_instance = AppGui()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # ========================================================================
    # AVVIA THREAD BLOCCO PROCESSI
    # ========================================================================

    _blocking_thread = threading.Thread(
        target=start_blocking_loop,
        daemon=True,
        name="BlockingThread"
    )
    _blocking_thread.start()
    print("[INFO] Thread di blocco avviato")

    # ========================================================================
    # AVVIA THREAD TRAY ICON
    # ========================================================================

    _tray_thread = threading.Thread(
        target=create_and_run_tray_icon,
        args=(_app_instance,),
        daemon=True,
        name="TrayThread"
    )
    _tray_thread.start()
    print("[INFO] Thread system tray avviato")

    # ========================================================================
    # MAINLOOP GUI
    # ========================================================================

    try:
        _app_instance.mainloop()

    except KeyboardInterrupt:
        print("\n[INFO] Interruzione da tastiera")

    except Exception as e:
        print(f"[ERROR] Errore mainloop: {e}")

    finally:
        print("[INFO] Chiusura applicazione...")
        cleanup_handlers()
        sys.exit(0)


if __name__ == "__main__":
    main()
