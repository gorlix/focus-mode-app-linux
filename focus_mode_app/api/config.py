"""
Integration configurations for the FastAPI backend.

Provides the environment variables and paths necessary to run the standalone
API server without conflicting with the main application configuration.
"""

from focus_mode_app.config import DATA_DIR, BASE_DIR

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

# Hardcoded for the current requirements, but can become environment variables
HA_WEBHOOK_URL = "http://homeassistant.local:8123/api/webhook/focus_mode_offline"
"""str: The endpoint to hit when the API server stops unexpectedly or shuts down."""

# ---------------------------------------------------------------------------- #
# LOGGING
# ---------------------------------------------------------------------------- #

API_LOG_FILE = BASE_DIR / "logs" / "focus_mode_api.log"
"""Path: Dedicated log file for API requests to maintain isolation from standard logs."""
