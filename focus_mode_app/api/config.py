"""
Integration configurations for the FastAPI backend.

Provides the environment variables and paths necessary to run the standalone
API server without conflicting with the main application configuration.
"""

import os
import sys
from pathlib import Path

from focus_mode_app.config import DATA_DIR

# ---------------------------------------------------------------------------- #
# SERVER CONFIGURATIONS
# ---------------------------------------------------------------------------- #

API_HOST = "0.0.0.0"
"""str: The interface the API should bind to. 0.0.0.0 allows remote connections."""

API_PORT = 8000
"""int: The underlying port for the Uvicorn server."""

# ---------------------------------------------------------------------------- #
# AUTHENTICATION
# ---------------------------------------------------------------------------- #

API_AUTH_TOKEN_FILE = DATA_DIR / "auth_token.txt"
"""Path: The file where the 32-character authentication token is stored."""

# ---------------------------------------------------------------------------- #
# WEBHOOK & NOTIFICATIONS
# ---------------------------------------------------------------------------- #

# Il webhook URL viene caricato a runtime da core.ha_config (data/ha_config.json).
# Non è definito qui per evitare che venga baked-in all'avvio: in questo modo
# l'URL aggiornato via GUI di impostazioni è applicato al prossimo dying gasp
# senza richiedere il riavvio dell'applicazione.

# ---------------------------------------------------------------------------- #
# LOGGING
# ---------------------------------------------------------------------------- #

if getattr(sys, "frozen", False):
    _xdg_cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    API_LOG_FILE = _xdg_cache / "focus_mode_app" / "focus_mode_api.log"
else:
    API_LOG_FILE = (
        Path(__file__).resolve().parent.parent / "logs" / "focus_mode_api.log"
    )
"""Path: Dedicated log file for API requests to maintain isolation from standard logs."""
