"""
Thread manager and lifecycle controller for the FastAPI/Uvicorn backend.

Provides a clean instantiation barrier so the main application (main.py)
doesn't need to understand Uvicorn configuration or threading semantics.
Includes the graceful shutdown mechanism and Dying Gasp webhook.
"""

import threading
from typing import Optional

import requests
import uvicorn

from focus_mode_app.api.server import app
from focus_mode_app.api.config import API_HOST, API_PORT
from focus_mode_app.api.logger import api_logger


_api_server: Optional[uvicorn.Server] = None
_api_thread: Optional[threading.Thread] = None


def _run_uvicorn() -> None:
    """
    Internal target function for the dedicated network thread.

    Initializes Uvicorn configuration dynamically and initiates the asyncio event loop
    for the REST API.
    """
    global _api_server
    config = uvicorn.Config(
        app=app,
        host=API_HOST,
        port=API_PORT,
        log_level="warning"
    )
    _api_server = uvicorn.Server(config=config)

    api_logger.info(f"Starting Uvicorn server on {API_HOST}:{API_PORT}")
    _api_server.run()


def start_api() -> None:
    """
    Spawns the Uvicorn HTTP server in a dedicated background thread.

    The thread is intentionally NOT set as a daemon thread, so the OS does not
    abruptly kill it when main.py exits, permitting graceful HTTP closures.
    """
    global _api_thread
    api_logger.info("Initializing API thread...")

    _api_thread = threading.Thread(
        target=_run_uvicorn,
        name="FocusModeApiThread",
        daemon=False  # Crucial for graceful shutdown
    )
    _api_thread.start()


def stop_api() -> None:
    """
    Gracefully terminate the Uvicorn server and issue the Dying Gasp webhook.

    1. Triggers an async-like HTTP POST to Home Assistant.
    2. Instructs Uvicorn to refuse new connections but finish inflight requests.
    3. Blocks (for a timeout) to wait for the thread to cleanly exit.
    """
    global _api_server, _api_thread

    # 1. Dying Gasp Webhook: notifica HA che l'app sta andando offline.
    #    L'URL viene letto a runtime da ha_config per supportare aggiornamenti
    #    senza riavvio. Se non configurato, il passo viene saltato silenziosamente.
    from focus_mode_app.core.ha_config import get_dying_gasp_url
    dying_gasp_url = get_dying_gasp_url()

    if not dying_gasp_url:
        api_logger.info("Nessun URL dying gasp configurato — webhook saltato.")
    else:
        api_logger.info(f"Invio Dying Gasp a: {dying_gasp_url}")
        try:
            requests.post(
                dying_gasp_url,
                json={"event": "dying_gasp", "status": "offline"},
                timeout=2.0
            )
            api_logger.info("Dying Gasp inviato con successo.")
        except requests.RequestException as e:
            api_logger.warning(f"Invio Dying Gasp fallito: {e}")

    # 2. Graceful Uvicorn Shutdown
    if _api_server is not None:
        api_logger.info("Signaling Uvicorn to exit gracefully.")
        _api_server.should_exit = True

    # 3. Thread Join
    if _api_thread is not None and _api_thread.is_alive():
        # Wait up to 3 seconds for active HTTP requests to finish executing
        _api_thread.join(timeout=3.0)
        api_logger.info("API Thread joined. Server offline.")
