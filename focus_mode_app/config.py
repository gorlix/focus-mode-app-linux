"""
config.py
Global configurations for the Focus Mode App.
Contains constants, file paths, and modifiable settings.
"""

import os
from pathlib import Path
from typing import Dict, Any

# ============================================================================
# FILE AND DIRECTORY PATHS
# ============================================================================

# Base directory of the project (where main.py is located)
BASE_DIR = Path(__file__).resolve().parent

# Directory for data persistence
DATA_DIR = BASE_DIR / "data"

# JSON file for saving blocked apps/webapps
DATA_FILE = DATA_DIR / "blocked_apps.json"

# JSON file for configuring auto-restore apps
RESTORE_CONFIG_FILE = DATA_DIR / "restore_config.json"

# JSON file for tracking the active session's killed apps (runtime backup)
SESSION_FILE = DATA_DIR / "session_backup.json"

# Directory for static assets (icons, images)
ASSETS_DIR = BASE_DIR / "assets"

# ============================================================================
# BLOCKING CONFIGURATIONS
# ============================================================================

# Process scanning interval (in seconds)
BLOCKING_INTERVAL = 2

# Initial blocking state on startup (True = active, False = deactivated)
BLOCKING_ACTIVE_ON_STARTUP = False

# ============================================================================
# SESSION RESTORE CONFIGURATIONS
# ============================================================================

# Auto-restore enabled by default
AUTO_RESTORE_ENABLED = True

# Delay before restoring apps (milliseconds)
# Allows the blocker to completely halt before restoration begins
RESTORE_DELAY_MS = 500

# Interval between consecutive app restorations (seconds)
RESTORE_INTERVAL = 0.3

# ============================================================================
# GUI CONFIGURATIONS
# ============================================================================

# Main window dimensions
WINDOW_WIDTH = 540
WINDOW_HEIGHT = 720  # Increased to accommodate the restore panel

# ttkbootstrap theme to use
# Options: "flatly", "cosmo", "litera", "minty", "lumen", "darkly", "cyborg", "superhero"
GUI_THEME = "flatly"

# Application Title
APP_TITLE = "Focus Mode App"

# ============================================================================
# SYSTEM TRAY CONFIGURATIONS
# ============================================================================

# Identifier name for the tray icon
TRAY_ID = "focus_mode_app"

# Tooltip text for the tray icon
TRAY_TOOLTIP = "Focus Mode App"

# ============================================================================
# NOTIFICATION CONFIGURATIONS
# ============================================================================

# Enable desktop notifications (e.g., notify-send on Linux)
DESKTOP_NOTIFICATIONS_ENABLED = True

# Icon name to use in notifications
NOTIFICATION_ICON = "dialog-information"

# Notification urgency (low, normal, critical)
NOTIFICATION_URGENCY = "normal"

# ============================================================================
# LOGGING CONFIGURATIONS
# ============================================================================

# Enable console logging output
CONSOLE_LOGGING = True

# Enable file logging output
FILE_LOGGING = False

# Path to the log file (if FILE_LOGGING is True)
LOG_FILE = BASE_DIR / "logs" / "focus_mode_app.log"

# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = "INFO"

# ============================================================================
# ADVANCED CONFIGURATIONS
# ============================================================================

# Timeout for process termination (in seconds)
PROCESS_KILL_TIMEOUT = 1

# Maximum number of attempts to kill a specific process
MAX_KILL_ATTEMPTS = 3

# Platform detected (for debugging/diagnostics)
# Values: "wayland", "x11", "unknown"
DETECTED_PLATFORM = "unknown"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def detect_platform() -> str:
    """Detect the active graphics platform (Wayland or X11).

    Returns:
        str: "wayland", "x11", or "unknown"
    """
    session_type = os.getenv("XDG_SESSION_TYPE", "").lower()

    if "wayland" in session_type:
        return "wayland"
    elif "x11" in session_type:
        return "x11"
    else:
        # Fallback: check DISPLAY environment variable
        if os.getenv("DISPLAY"):
            return "x11"
        return "unknown"


def ensure_directories() -> None:
    """Ensure that all necessary data and asset directories exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    if FILE_LOGGING:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    print("[INFO] Directories verified/created")
    print(f"[INFO] Platform detected: {DETECTED_PLATFORM}")


def load_config() -> Dict[str, Any]:
    """Load and return a dictionary containing all configurations.

    Creates missing directories as a side effect.

    Returns:
        Dict[str, Any]: A dictionary mapping configuration keys to values.
    """
    ensure_directories()

    config = {
        # Paths
        "base_dir": BASE_DIR,
        "data_dir": DATA_DIR,
        "data_file": DATA_FILE,
        "restore_config_file": RESTORE_CONFIG_FILE,
        "session_file": SESSION_FILE,
        "assets_dir": ASSETS_DIR,
        "log_file": LOG_FILE,
        # Blocking
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
        # Notifications
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


def get_data_file_path() -> Path:
    """Return the absolute path to the main JSON data file.

    Returns:
        Path: Path to blocked_apps.json.
    """
    return DATA_FILE


def get_restore_config_path() -> Path:
    """Return the absolute path to the restore configuration JSON file.

    Returns:
        Path: Path to restore_config.json.
    """
    return RESTORE_CONFIG_FILE


def get_session_file_path() -> Path:
    """Return the absolute path to the backup session JSON file.

    Returns:
        Path: Path to session_backup.json.
    """
    return SESSION_FILE


# Detect the platform upon import
DETECTED_PLATFORM = detect_platform()


# ============================================================================
# APPLICATION METADATA
# ============================================================================

APP_NAME = "Focus Mode App"
APP_VERSION = "1.0.1"
APP_AUTHOR = "Gorlix"
APP_DESCRIPTION = "Block distracting apps and websites to boost productivity"


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    # Paths
    "BASE_DIR",
    "DATA_DIR",
    "DATA_FILE",
    "RESTORE_CONFIG_FILE",
    "SESSION_FILE",
    "ASSETS_DIR",
    # Blocking configurations
    "BLOCKING_INTERVAL",
    "BLOCKING_ACTIVE_ON_STARTUP",
    "PROCESS_KILL_TIMEOUT",
    "MAX_KILL_ATTEMPTS",
    # Session Restore
    "AUTO_RESTORE_ENABLED",
    "RESTORE_DELAY_MS",
    "RESTORE_INTERVAL",
    # GUI
    "WINDOW_WIDTH",
    "WINDOW_HEIGHT",
    "GUI_THEME",
    "APP_TITLE",
    # Tray
    "TRAY_ID",
    "TRAY_TOOLTIP",
    # Notifications
    "DESKTOP_NOTIFICATIONS_ENABLED",
    "NOTIFICATION_ICON",
    "NOTIFICATION_URGENCY",
    # Logging
    "CONSOLE_LOGGING",
    "FILE_LOGGING",
    "LOG_FILE",
    "LOG_LEVEL",
    # Platform
    "DETECTED_PLATFORM",
    # Functions
    "load_config",
    "get_data_file_path",
    "get_restore_config_path",
    "get_session_file_path",
    "ensure_directories",
    "detect_platform",
    # App Info
    "APP_NAME",
    "APP_VERSION",
    "APP_AUTHOR",
    "APP_DESCRIPTION",
]
