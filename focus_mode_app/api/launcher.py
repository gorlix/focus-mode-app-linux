"""
Thread manager and lifecycle controller for the FastAPI/Uvicorn backend
and the Home Assistant native app client.

On start: launches uvicorn + initialises HAClient + starts WS listener.
On stop:  sends dying gasp + stops WS listener + gracefully shuts uvicorn.
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
    global _api_server
    config = uvicorn.Config(
        app=app,
        host=API_HOST,
        port=API_PORT,
        log_level="warning",
    )
    _api_server = uvicorn.Server(config=config)
    api_logger.info("Starting Uvicorn server on %s:%s", API_HOST, API_PORT)
    _api_server.run()


def start_api() -> None:
    """
    Start the Uvicorn HTTP server and the HA native app client (if configured).
    """
    global _api_thread

    _api_thread = threading.Thread(
        target=_run_uvicorn,
        name="FocusModeApiThread",
        daemon=False,
    )
    _api_thread.start()

    _start_ha_client()


def stop_api() -> None:
    """
    Send dying gasp, stop HA client, then gracefully shut down Uvicorn.
    """
    _stop_ha_client()

    if _api_server is not None:
        api_logger.info("Signaling Uvicorn to exit gracefully.")
        _api_server.should_exit = True

    if _api_thread is not None and _api_thread.is_alive():
        _api_thread.join(timeout=3.0)
        api_logger.info("API thread joined. Server offline.")


# ------------------------------------------------------------------
# HA client lifecycle helpers
# ------------------------------------------------------------------

def _start_ha_client() -> None:
    """Initialise HAClient from saved config and start the WS listener."""
    from focus_mode_app.core.ha_config import load_ha_config
    from focus_mode_app.core import ha_client as _ha

    cfg = load_ha_config()
    ha_url = cfg.get("ha_url", "").strip()
    llat = cfg.get("llat", "").strip()
    webhook_id = cfg.get("webhook_id", "").strip()

    if not (ha_url and llat):
        api_logger.info("HA client not configured (ha_url/llat missing) — skipping.")
        return

    client = _ha.init_client(ha_url=ha_url, llat=llat, webhook_id=webhook_id)

    if webhook_id:
        # Register sensors (idempotent) then start WS listener
        threading.Thread(
            target=_register_and_listen,
            args=(client,),
            daemon=True,
            name="HAClientInit",
        ).start()
    else:
        api_logger.info("HA client configured but not yet registered (no webhook_id).")


def _register_and_listen(client) -> None:
    """Register sensors and start the WebSocket listener (runs in a thread)."""
    try:
        client.register_sensors()
    except Exception as exc:
        api_logger.warning("Sensor registration failed: %s", exc)
    client.start_command_listener()


def _stop_ha_client() -> None:
    """Send dying gasp and stop the WS listener."""
    from focus_mode_app.core import ha_client as _ha
    from focus_mode_app.core.ha_config import get_dying_gasp_url

    client = _ha.get_client()
    if client and client.webhook_id:
        client.send_dying_gasp()
        client.stop_command_listener()
        return

    # Legacy fallback dying gasp
    dying_gasp_url = get_dying_gasp_url()
    if dying_gasp_url:
        api_logger.info("Sending legacy dying gasp to %s", dying_gasp_url)
        try:
            requests.post(
                dying_gasp_url,
                json={"event": "dying_gasp", "status": "offline"},
                timeout=2.0,
            )
        except requests.RequestException as exc:
            api_logger.warning("Legacy dying gasp failed: %s", exc)
