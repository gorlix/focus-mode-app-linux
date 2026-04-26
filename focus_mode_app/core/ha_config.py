"""
core/ha_config.py
Persistenza della configurazione per l'integrazione con Home Assistant.

Gestisce il salvataggio e il caricamento di:
- URL del webhook "dying gasp" (notifica spegnimento app → HA)
- URL del webhook eventi di stato (push real-time cambio stato → HA)
- Long-Lived Access Token HA (per future chiamate API verso HA)
"""

import json
import os
from pathlib import Path

from focus_mode_app.config import DATA_DIR

HA_CONFIG_FILE: Path = DATA_DIR / "ha_config.json"

_DEFAULTS: dict = {
    "dying_gasp_url": "",
    "state_event_url": "",
    "llat": "",
}


def load_ha_config() -> dict:
    """
    Carica la configurazione HA dal file JSON.

    Returns:
        dict con chiavi dying_gasp_url, state_event_url, llat.
        In caso di file mancante o corrotto ritorna i valori di default.
    """
    if not HA_CONFIG_FILE.exists():
        return dict(_DEFAULTS)

    try:
        with open(HA_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {**_DEFAULTS, **data}

    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULTS)


def save_ha_config(dying_gasp_url: str, state_event_url: str, llat: str) -> bool:
    """
    Salva la configurazione HA su disco con permessi ristretti (0o600).

    Args:
        dying_gasp_url: URL webhook HA notifica spegnimento app.
        state_event_url: URL webhook HA per push cambio stato real-time.
        llat: Home Assistant Long-Lived Access Token.

    Returns:
        True se il salvataggio è riuscito, False altrimenti.
    """
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        payload = {
            "dying_gasp_url": dying_gasp_url,
            "state_event_url": state_event_url,
            "llat": llat,
        }

        with open(HA_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)

        try:
            os.chmod(HA_CONFIG_FILE, 0o600)
        except OSError:
            pass

        return True

    except Exception as e:
        print(f"[ERROR] ha_config: impossibile salvare: {e}")
        return False


def get_dying_gasp_url() -> str:
    """URL webhook HA per il dying gasp (notifica spegnimento). Stringa vuota se non configurato."""
    return load_ha_config().get("dying_gasp_url", "")


def get_state_event_url() -> str:
    """URL webhook HA per push eventi di stato. Stringa vuota se non configurato."""
    return load_ha_config().get("state_event_url", "")


def get_llat() -> str:
    """Home Assistant Long-Lived Access Token. Stringa vuota se non configurato."""
    return load_ha_config().get("llat", "")


__all__ = [
    "HA_CONFIG_FILE",
    "load_ha_config",
    "save_ha_config",
    "get_dying_gasp_url",
    "get_state_event_url",
    "get_llat",
]
