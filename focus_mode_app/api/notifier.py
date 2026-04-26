"""
api/notifier.py
Notifiche push verso Home Assistant al cambio di stato dell'applicazione.

Ogni volta che lo stato del blocker, del lock o del restore cambia via API,
questa funzione invia un POST fire-and-forget al webhook HA configurato.
L'invio avviene in un thread daemon separato per non bloccare il thread API.
"""

import threading
import requests

from focus_mode_app.api.logger import api_logger


def _post_event(url: str, payload: dict) -> None:
    """Target del thread daemon — invia il POST e logga l'esito."""
    try:
        requests.post(url, json=payload, timeout=3.0)
        api_logger.debug(f"Evento stato inviato a HA: {payload.get('event')}")
    except requests.RequestException as e:
        api_logger.warning(f"Invio evento stato a HA fallito: {e}")


def notify_state_change(event: str, **extra) -> None:
    """
    Invia un evento di cambio stato a Home Assistant via webhook configurato.

    L'URL viene letto a runtime da ha_config; se non è configurato la funzione
    ritorna immediatamente senza effetti. L'invio è asincrono (thread daemon)
    per non bloccare il thread API.

    Args:
        event: Tipo di evento (es. "focus_toggled", "lock_activated", "restore_changed").
        **extra: Campi aggiuntivi inclusi nel payload JSON (es. active=True, mode="ha").
    """
    from focus_mode_app.core.ha_config import get_state_event_url
    url = get_state_event_url()

    if not url:
        return

    payload = {"event": event, **extra}
    threading.Thread(target=_post_event, args=(url, payload), daemon=True).start()
