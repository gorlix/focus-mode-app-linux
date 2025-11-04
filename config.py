"""
config.py
Configurazioni globali per l'applicazione Focus Mode App.
Contiene costanti, percorsi file e impostazioni modificabili.
"""

import os
from pathlib import Path

# ============================================================================
# PERCORSI FILE E DIRECTORY
# ============================================================================

# Directory base del progetto (dove si trova main.py)
BASE_DIR = Path(__file__).resolve().parent

# Directory per i dati
DATA_DIR = BASE_DIR / "data"

# File JSON per salvare app/webapp bloccate
DATA_FILE = DATA_DIR / "blocked_apps.json"

# File JSON per configurazione app da ripristinare
RESTORE_CONFIG_FILE = DATA_DIR / "restore_config.json"

# File JSON per sessione app killate (runtime backup)
SESSION_FILE = DATA_DIR / "session_backup.json"

# Directory per assets (icone, immagini)
ASSETS_DIR = BASE_DIR / "assets"

# ============================================================================
# CONFIGURAZIONI BLOCCO
# ============================================================================

# Intervallo di controllo processi (in secondi)
BLOCKING_INTERVAL = 2

# Stato iniziale del blocco all'avvio (True = attivo, False = disattivato)
BLOCKING_ACTIVE_ON_STARTUP = False

# ============================================================================
# CONFIGURAZIONI SESSION RESTORE
# ============================================================================

# Auto-restore abilitato di default
AUTO_RESTORE_ENABLED = True

# Delay prima di ripristinare app (millisecondi)
# Permette al blocco di fermarsi completamente prima di ripristinare
RESTORE_DELAY_MS = 500

# Intervallo tra ripristino di app successive (secondi)
RESTORE_INTERVAL = 0.3

# ============================================================================
# CONFIGURAZIONI GUI
# ============================================================================

# Dimensioni finestra principale
WINDOW_WIDTH = 540
WINDOW_HEIGHT = 720  # 🔄 Aumentato per il nuovo panel restore

# Tema ttkbootstrap da utilizzare
# Opzioni: "flatly", "cosmo", "litera", "minty", "lumen", "darkly", "cyborg", "superhero"
GUI_THEME = "flatly"

# Titolo dell'applicazione
APP_TITLE = "Focus Mode App"

# ============================================================================
# CONFIGURAZIONI SYSTEM TRAY
# ============================================================================

# Nome identificativo del tray icon
TRAY_ID = "focus_mode_app"

# Tooltip del tray icon
TRAY_TOOLTIP = "Focus Mode App"

# ============================================================================
# CONFIGURAZIONI NOTIFICHE
# ============================================================================

# Abilita notifiche desktop (notify-send su Linux)
DESKTOP_NOTIFICATIONS_ENABLED = True

# Icon da usare nelle notifiche
NOTIFICATION_ICON = "dialog-information"

# Urgenza notifiche (low, normal, critical)
NOTIFICATION_URGENCY = "normal"

# ============================================================================
# CONFIGURAZIONI LOGGING
# ============================================================================

# Abilita logging su console
CONSOLE_LOGGING = True

# Abilita logging su file
FILE_LOGGING = False

# Percorso file di log (se FILE_LOGGING è True)
LOG_FILE = BASE_DIR / "logs" / "focus_mode_app.log"

# Livello di logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = "INFO"

# ============================================================================
# CONFIGURAZIONI AVANZATE
# ============================================================================

# Timeout per la terminazione processi (in secondi)
PROCESS_KILL_TIMEOUT = 1

# Numero massimo di tentativi per killare un processo
MAX_KILL_ATTEMPTS = 3

# Piattaforma rilevata (per debug)
# Valori: "wayland", "x11", "unknown"
DETECTED_PLATFORM = "unknown"

# ============================================================================
# FUNZIONI DI UTILITÀ
# ============================================================================

def detect_platform() -> str:
    """
    Rileva la piattaforma grafica in uso (Wayland o X11).

    Returns:
        str: "wayland", "x11", o "unknown"
    """
    session_type = os.getenv('XDG_SESSION_TYPE', '').lower()

    if 'wayland' in session_type:
        return 'wayland'
    elif 'x11' in session_type:
        return 'x11'
    else:
        # Fallback: controlla DISPLAY variable
        if os.getenv('DISPLAY'):
            return 'x11'
        return 'unknown'


def ensure_directories():
    """
    Crea le directory necessarie se non esistono.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    if FILE_LOGGING:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Directory verificate/create")
    print(f"[INFO] Platform detected: {DETECTED_PLATFORM}")


def load_config():
    """
    Carica e ritorna un dizionario con tutte le configurazioni.
    Crea le directory necessarie.

    Returns:
        dict: Dizionario con tutte le configurazioni
    """
    ensure_directories()

    config = {
        # Percorsi
        "base_dir": BASE_DIR,
        "data_dir": DATA_DIR,
        "data_file": DATA_FILE,
        "restore_config_file": RESTORE_CONFIG_FILE,
        "session_file": SESSION_FILE,
        "assets_dir": ASSETS_DIR,
        "log_file": LOG_FILE,

        # Blocco
        "blocking_interval": BLOCKING_INTERVAL,
        "blocking_active_on_startup": BLOCKING_ACTIVE_ON_STARTUP,
        "process_kill_timeout": PROCESS_KILL_TIMEOUT,
        "max_kill_attempts": MAX_KILL_ATTEMPTS,

        # Session Restore
        "auto_restore_enabled": AUTO_RESTORE_ENABLED,
        "restore_delay_ms": RESTORE_DELAY_MS,
        "restore_interval": RESTORE_INTERVAL,

        # GUI
        "window_width": WINDOW_WIDTH,
        "window_height": WINDOW_HEIGHT,
        "gui_theme": GUI_THEME,
        "app_title": APP_TITLE,

        # System Tray
        "tray_id": TRAY_ID,
        "tray_tooltip": TRAY_TOOLTIP,

        # Notifiche
        "desktop_notifications_enabled": DESKTOP_NOTIFICATIONS_ENABLED,
        "notification_icon": NOTIFICATION_ICON,
        "notification_urgency": NOTIFICATION_URGENCY,

        # Logging
        "console_logging": CONSOLE_LOGGING,
        "file_logging": FILE_LOGGING,
        "log_level": LOG_LEVEL,

        # Platform
        "detected_platform": DETECTED_PLATFORM,
    }

    return config


def get_data_file_path():
    """
    Ritorna il percorso completo del file dati JSON.

    Returns:
        Path: Percorso del file blocked_apps.json
    """
    return DATA_FILE


def get_restore_config_path():
    """
    Ritorna il percorso del file configurazione restore.

    Returns:
        Path: Percorso del file restore_config.json
    """
    return RESTORE_CONFIG_FILE


def get_session_file_path():
    """
    Ritorna il percorso del file sessione.

    Returns:
        Path: Percorso del file session_backup.json
    """
    return SESSION_FILE


# Rileva piattaforma all'import
DETECTED_PLATFORM = detect_platform()

# ============================================================================
# INFORMAZIONI APPLICAZIONE
# ============================================================================

APP_NAME = "Focus Mode App"
APP_VERSION = "1.0.1"  # 🔄 Aggiornato a 1.0.1
APP_AUTHOR = "Gorlix"
APP_DESCRIPTION = "Block distracting apps and websites to boost productivity"

# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    # Percorsi
    'BASE_DIR',
    'DATA_DIR',
    'DATA_FILE',
    'RESTORE_CONFIG_FILE',
    'SESSION_FILE',
    'ASSETS_DIR',

    # Configurazioni blocco
    'BLOCKING_INTERVAL',
    'BLOCKING_ACTIVE_ON_STARTUP',
    'PROCESS_KILL_TIMEOUT',
    'MAX_KILL_ATTEMPTS',

    # Session Restore
    'AUTO_RESTORE_ENABLED',
    'RESTORE_DELAY_MS',
    'RESTORE_INTERVAL',

    # GUI
    'WINDOW_WIDTH',
    'WINDOW_HEIGHT',
    'GUI_THEME',
    'APP_TITLE',

    # Tray
    'TRAY_ID',
    'TRAY_TOOLTIP',

    # Notifiche
    'DESKTOP_NOTIFICATIONS_ENABLED',
    'NOTIFICATION_ICON',
    'NOTIFICATION_URGENCY',

    # Logging
    'CONSOLE_LOGGING',
    'FILE_LOGGING',
    'LOG_FILE',
    'LOG_LEVEL',

    # Platform
    'DETECTED_PLATFORM',

    # Funzioni
    'load_config',
    'get_data_file_path',
    'get_restore_config_path',
    'get_session_file_path',
    'ensure_directories',
    'detect_platform',

    # Info app
    'APP_NAME',
    'APP_VERSION',
    'APP_AUTHOR',
    'APP_DESCRIPTION',
]
