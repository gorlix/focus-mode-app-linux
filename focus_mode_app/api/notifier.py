"""
api/notifier.py
Notifiche push verso Home Assistant al cambio di stato dell'applicazione.

Strategia:
  1. Se il client nativo (ha_client) è configurato con webhook_id → push
     completo in formato update_sensor_states (native app format).
  2. Altrimenti → fallback al formato legacy (event POST all'URL configurato).

In entrambi i casi l'invio è fire-and-forget (thread daemon).
"""

import threading

import requests

from focus_mode_app.api.logger import api_logger


def _post_event(url: str, payload: dict) -> None:
    try:
        requests.post(url, json=payload, timeout=3.0)
        api_logger.debug("Evento legacy inviato a HA: %s", payload.get("event"))
    except requests.RequestException as exc:
        api_logger.warning("Invio evento legacy a HA fallito: %s", exc)


def notify_state_change(event: str, **extra) -> None:
    """
    Notifica HA del cambio di stato.

    Usa il client nativo (update_sensor_states) quando disponibile;
    altrimenti invia il formato legacy via URL webhook configurato.

    Args:
        event: Tipo di evento (es. "focus_toggled"). Usato solo nel fallback legacy.
        **extra: Campi aggiuntivi per il payload legacy (es. active=True).
    """
    # Native client path
    from focus_mode_app.core import ha_client as _ha

    if _ha.push_current_state():
        return

    # Legacy fallback
    from focus_mode_app.core.ha_config import get_state_event_url

    url = get_state_event_url()
    if not url:
        return

    payload = {"event": event, **extra}
    threading.Thread(target=_post_event, args=(url, payload), daemon=True).start()
