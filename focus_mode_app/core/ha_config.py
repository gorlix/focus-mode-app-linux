"""
core/ha_config.py
Persistenza della configurazione per l'integrazione con Home Assistant.

Gestisce il salvataggio e il caricamento di:
- URL del webhook "dying gasp" (notifica spegnimento app → HA)
- URL del webhook eventi di stato (push real-time cambio stato → HA)
- Long-Lived Access Token HA (per future chiamate API verso HA)
"""

import json
import logging
import os
from pathlib import Path

from focus_mode_app.config import DATA_DIR

_LOGGER = logging.getLogger(__name__)

HA_CONFIG_FILE: Path = DATA_DIR / "ha_config.json"

_DEFAULTS: dict = {
    "ha_url": "",
    "llat": "",
    "webhook_id": "",
    # Legacy fields kept for backward compat with existing ha_config.json
    "dying_gasp_url": "",
    "state_event_url": "",
}


def load_ha_config() -> dict:
    """
    Carica la configurazione HA dal file JSON.

    Returns:
        dict con chiavi dying_gasp_url, state_event_url, llat.
        In caso di file mancante o corrotto ritorna i valori di default.
    """
    if not HA_CONFIG_FILE.exists():
        _LOGGER.debug("Config file not found, using defaults")
        return dict(_DEFAULTS)

    try:
        with open(HA_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        cfg = {**_DEFAULTS, **data}
        _LOGGER.debug(
            "Config loaded: ha_url=%s webhook_id=%s llat=%s",
            cfg.get("ha_url") or "(empty)",
            cfg.get("webhook_id") or "(empty)",
            "***" if cfg.get("llat") else "(empty)",
        )
        return cfg

    except (json.JSONDecodeError, OSError) as exc:
        _LOGGER.warning("Config load failed (%s), using defaults", exc)
        return dict(_DEFAULTS)


def save_ha_config(
    llat: str,
    ha_url: str = "",
    webhook_id: str = "",
    dying_gasp_url: str = "",
    state_event_url: str = "",
) -> bool:
    """
    Salva la configurazione HA su disco con permessi ristretti (0o600).

    Args:
        llat: Home Assistant Long-Lived Access Token.
        ha_url: URL base di Home Assistant (es. https://homeassistant.local:8123).
        webhook_id: Webhook ID ricevuto dopo la registrazione del dispositivo.
        dying_gasp_url: (legacy) URL webhook dying gasp.
        state_event_url: (legacy) URL webhook eventi di stato.

    Returns:
        True se il salvataggio è riuscito, False altrimenti.
    """
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        existing = load_ha_config()
        payload = {
            **existing,
            "ha_url": ha_url or existing.get("ha_url", ""),
            "llat": llat,
            "webhook_id": webhook_id or existing.get("webhook_id", ""),
            "dying_gasp_url": dying_gasp_url or existing.get("dying_gasp_url", ""),
            "state_event_url": state_event_url or existing.get("state_event_url", ""),
        }

        with open(HA_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)

        try:
            os.chmod(HA_CONFIG_FILE, 0o600)
        except OSError:
            pass

        _LOGGER.info(
            "Config saved → %s  ha_url=%s  webhook_id=%s  llat=%s",
            HA_CONFIG_FILE,
            payload["ha_url"] or "(empty)",
            payload["webhook_id"] or "(empty)",
            "***" if payload["llat"] else "(empty)",
        )
        return True

    except Exception as exc:
        _LOGGER.error("Save failed: %s", exc)
        return False


def get_ha_url() -> str:
    """URL base di Home Assistant. Stringa vuota se non configurato."""
    return load_ha_config().get("ha_url", "")


def get_webhook_id() -> str:
    """Webhook ID ricevuto dopo la registrazione. Stringa vuota se non registrato."""
    return load_ha_config().get("webhook_id", "")


def save_webhook_id(webhook_id: str) -> bool:
    """Salva solo il webhook_id (dopo registrazione)."""
    existing = load_ha_config()
    return save_ha_config(
        llat=existing.get("llat", ""),
        ha_url=existing.get("ha_url", ""),
        webhook_id=webhook_id,
    )


def get_dying_gasp_url() -> str:
    """URL webhook dying gasp (legacy). Stringa vuota se non configurato."""
    cfg = load_ha_config()
    if cfg.get("ha_url") and cfg.get("webhook_id"):
        return f"{cfg['ha_url'].rstrip('/')}/api/webhook/{cfg['webhook_id']}"
    return cfg.get("dying_gasp_url", "")


def get_state_event_url() -> str:
    """URL webhook eventi di stato (legacy). Stringa vuota se non configurato."""
    cfg = load_ha_config()
    if cfg.get("ha_url") and cfg.get("webhook_id"):
        return f"{cfg['ha_url'].rstrip('/')}/api/webhook/{cfg['webhook_id']}"
    return cfg.get("state_event_url", "")


def get_llat() -> str:
    """Home Assistant Long-Lived Access Token. Stringa vuota se non configurato."""
    return load_ha_config().get("llat", "")


__all__ = [
    "HA_CONFIG_FILE",
    "load_ha_config",
    "save_ha_config",
    "save_webhook_id",
    "get_ha_url",
    "get_webhook_id",
    "get_dying_gasp_url",
    "get_state_event_url",
    "get_llat",
]
