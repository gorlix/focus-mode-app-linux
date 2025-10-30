"""
main.py
Entry point principale dell'applicazione Modalità Studio.
"""

import threading
from config import load_config
from core.storage import load_blocked_items
from core.blocker import start_blocking_loop
from gui.main_window import AppGui
from utils.tray_icon import create_and_run_tray_icon, stop_tray_icon


def main():
    """Funzione principale che avvia l'applicazione."""
    print("[INFO] Avvio Modalità Studio...")
    
    # Carica configurazione e crea directory necessarie
    load_config()
    
    # Carica elementi bloccati salvati
    load_blocked_items()
    
    # Crea GUI
    app = AppGui()
    
    # ========================================================================
    # AVVIA THREAD BLOCCO PROCESSI
    # ========================================================================
    blocking_thread = threading.Thread(
        target=start_blocking_loop,
        daemon=True,
        name="BlockingThread"
    )
    blocking_thread.start()
    print("[INFO] Thread di blocco avviato")
    
    # ========================================================================
    # AVVIA THREAD TRAY ICON
    # ========================================================================
    tray_thread = threading.Thread(
        target=create_and_run_tray_icon,
        args=(app,),
        daemon=True,
        name="TrayThread"
    )
    tray_thread.start()
    print("[INFO] Thread system tray avviato")
    
    # ========================================================================
    # MAINLOOP GUI
    # ========================================================================
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("\n[INFO] Interruzione da tastiera")
    finally:
        print("[INFO] Chiusura applicazione...")
        stop_tray_icon()


if __name__ == "__main__":
    main()

