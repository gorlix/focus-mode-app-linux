"""
config.py
Configurazioni globali per l'applicazione Modalità Studio.
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
# CONFIGURAZIONI GUI
# ============================================================================

# Dimensioni finestra principale
WINDOW_WIDTH = 540
WINDOW_HEIGHT = 620

# Tema ttkbootstrap da utilizzare
# Opzioni: "flatly", "cosmo", "litera", "minty", "lumen", "darkly", "cyborg", "superhero"
GUI_THEME = "flatly"

# Titolo dell'applicazione
APP_TITLE = "Modalità Studio"

# ============================================================================
# CONFIGURAZIONI SYSTEM TRAY
# ============================================================================

# Nome identificativo del tray icon
TRAY_ID = "modalita_studio"

# Tooltip del tray icon
TRAY_TOOLTIP = "Modalità Studio"

# ============================================================================
# CONFIGURAZIONI LOGGING
# ============================================================================

# Abilita logging su console
CONSOLE_LOGGING = True

# Abilita logging su file
FILE_LOGGING = False

# Percorso file di log (se FILE_LOGGING è True)
LOG_FILE = BASE_DIR / "logs" / "modalita_studio.log"

# Livello di logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = "INFO"

# ============================================================================
# CONFIGURAZIONI AVANZATE
# ============================================================================

# Timeout per la terminazione processi (in secondi)
PROCESS_KILL_TIMEOUT = 1

# Numero massimo di tentativi per killare un processo
MAX_KILL_ATTEMPTS = 3

# ============================================================================
# FUNZIONI DI UTILITÀ
# ============================================================================

def ensure_directories():
    """
    Crea le directory necessarie se non esistono.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    
    if FILE_LOGGING:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"[INFO] Directory verificate/create")


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
        "assets_dir": ASSETS_DIR,
        "log_file": LOG_FILE,
        
        # Blocco
        "blocking_interval": BLOCKING_INTERVAL,
        "blocking_active_on_startup": BLOCKING_ACTIVE_ON_STARTUP,
        "process_kill_timeout": PROCESS_KILL_TIMEOUT,
        "max_kill_attempts": MAX_KILL_ATTEMPTS,
        
        # GUI
        "window_width": WINDOW_WIDTH,
        "window_height": WINDOW_HEIGHT,
        "gui_theme": GUI_THEME,
        "app_title": APP_TITLE,
        
        # System Tray
        "tray_id": TRAY_ID,
        "tray_tooltip": TRAY_TOOLTIP,
        
        # Logging
        "console_logging": CONSOLE_LOGGING,
        "file_logging": FILE_LOGGING,
        "log_level": LOG_LEVEL,
    }
    
    return config


def get_data_file_path():
    """
    Ritorna il percorso completo del file dati JSON.
    
    Returns:
        Path: Percorso del file blocked_apps.json
    """
    return DATA_FILE


# ============================================================================
# INFORMAZIONI APPLICAZIONE
# ============================================================================

APP_NAME = "Modalità Studio"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Gorlix"
APP_DESCRIPTION = "Blocca app e webapp durante le sessioni di studio"

# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    'BASE_DIR',
    'DATA_DIR',
    'DATA_FILE',
    'ASSETS_DIR',
    'BLOCKING_INTERVAL',
    'BLOCKING_ACTIVE_ON_STARTUP',
    'WINDOW_WIDTH',
    'WINDOW_HEIGHT',
    'GUI_THEME',
    'APP_TITLE',
    'TRAY_ID',
    'TRAY_TOOLTIP',
    'load_config',
    'get_data_file_path',
    'ensure_directories',
]

