"""
core/storage.py
Gestione del salvataggio e caricamento dei dati (lista app/webapp bloccate).
Include migrazione automatica dal vecchio formato.
"""

import json
from typing import List, Dict

from focus_mode_app.config import get_data_file_path

# Lista globale degli elementi bloccati
# Ogni elemento è un dict: {"name": "...", "type": "app" | "webapp"}
blocked_items: List[Dict[str, str]] = []


# ============================================================================
# FUNZIONI DI SALVATAGGIO
# ============================================================================


def save_blocked_items() -> bool:
    """Save the list of blocked items to the JSON configuration file.

    Returns:
        bool: True if the save was successful, False otherwise.
    """
    data_file = get_data_file_path()

    try:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(blocked_items, f, indent=4, ensure_ascii=False)

        print(f"[INFO] Lista salvata in {data_file}")
        return True

    except PermissionError:
        print(f"[ERROR] Permesso negato per scrittura su {data_file}")
        return False

    except Exception as e:
        print(f"[ERROR] Errore durante il salvataggio: {e}")
        return False


# ============================================================================
# FUNZIONI DI CARICAMENTO
# ============================================================================


def load_blocked_items() -> bool:
    """Load the list of blocked items from the JSON configuration file.

    Automatically handles migration if the legacy JSON format is detected.

    Returns:
        bool: True if the load was successful, False otherwise.
    """
    global blocked_items
    data_file = get_data_file_path()

    if not data_file.exists():
        print(f"[INFO] File di configurazione non trovato: {data_file}")
        print("[INFO] Verrà creato automaticamente al primo salvataggio")
        blocked_items = []
        return True

    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Controlla se è il vecchio formato (dict con "apps_native" e "webapp_elements")
        if isinstance(data, dict) and (
            "apps_native" in data or "webapp_elements" in data
        ):
            print("[INFO] Rilevato vecchio formato, migrazione in corso...")
            blocked_items = migrate_old_format(data)
            # Salva subito nel nuovo formato
            save_blocked_items()
            print("[INFO] Migrazione completata!")

        # Nuovo formato (lista di dict)
        elif isinstance(data, list):
            blocked_items = data
            print(f"[INFO] Lista caricata da {data_file}")

        else:
            print(
                "[WARNING] Formato file non riconosciuto, inizializzazione lista vuota"
            )
            blocked_items = []

        print(f"[INFO] Elementi bloccati caricati: {len(blocked_items)}")
        return True

    except json.JSONDecodeError as e:
        print(f"[ERROR] File JSON corrotto: {e}")
        print("[INFO] Inizializzazione lista vuota")
        blocked_items = []
        return False

    except Exception as e:
        print(f"[ERROR] Errore durante il caricamento: {e}")
        blocked_items = []
        return False


# ============================================================================
# MIGRAZIONE FORMATO
# ============================================================================


def migrate_old_format(old_data: dict) -> List[Dict[str, str]]:
    """Convert the old JSON configuration format to the new format.

    Legacy format:
    {
        "apps_native": ["firefox", "telegram"],
        "webapp_elements": ["web.whatsapp.com"]
    }

    New format:
    [
        {"name": "firefox", "type": "app"},
        {"name": "telegram", "type": "app"},
        {"name": "web.whatsapp.com", "type": "webapp"}
    ]

    Args:
        old_data (dict): Dictionary reflecting the legacy format.

    Returns:
        List[Dict[str, str]]: The converted list in the new format.
    """
    migrated_items = []

    # Migra app native
    for app_name in old_data.get("apps_native", []):
        migrated_items.append({"name": app_name, "type": "app"})

    # Migra webapp
    for webapp_url in old_data.get("webapp_elements", []):
        migrated_items.append({"name": webapp_url, "type": "webapp"})

    print(f"[INFO] Migrati {len(migrated_items)} elementi dal vecchio formato")
    return migrated_items


# ============================================================================
# FUNZIONI DI GESTIONE LISTA
# ============================================================================


def add_blocked_item(name: str, item_type: str) -> bool:
    """Add a new item to the active blocklist.

    Args:
        name (str): Name of the application or URL of the web application.
        item_type (str): The type of item, strictly "app" or "webapp".

    Returns:
        bool: True if successfully added, False if invalid type or already exists.
    """
    if item_type not in ["app", "webapp"]:
        print(f"[WARNING] Tipo non valido: {item_type}")
        return False

    # Controlla duplicati
    for item in blocked_items:
        if item["name"] == name and item["type"] == item_type:
            print(f"[WARNING] Elemento già presente: {name} ({item_type})")
            return False

    # Aggiungi nuovo elemento
    new_item = {"name": name, "type": item_type}
    blocked_items.append(new_item)

    # Salva automaticamente
    save_blocked_items()
    print(f"[INFO] Aggiunto: {name} ({item_type})")

    return True


def remove_blocked_item(index: int) -> bool:
    """Remove an item from the blocklist by its index.

    Args:
        index (int): The integer list index of the item to remove.

    Returns:
        bool: True if removed successfully, False if the index is out of bounds.
    """
    if 0 <= index < len(blocked_items):
        removed_item = blocked_items.pop(index)
        save_blocked_items()
        print(f"[INFO] Rimosso: {removed_item['name']} ({removed_item['type']})")
        return True
    else:
        print(f"[WARNING] Indice non valido: {index}")
        return False


def get_blocked_items() -> List[Dict[str, str]]:
    """Return a copy of the complete blocklist.

    Returns:
        List[Dict[str, str]]: A list of dictionaries representing the blocked items.
    """
    return blocked_items.copy()


def get_blocked_apps() -> List[str]:
    """Retrieve only the blocked native applications.

    Returns:
        List[str]: A list of native application names.
    """
    return [item["name"] for item in blocked_items if item["type"] == "app"]


def get_blocked_webapps() -> List[str]:
    """Retrieve only the blocked web applications.

    Returns:
        List[str]: A list of web usage URLs or string identifiers.
    """
    return [item["name"] for item in blocked_items if item["type"] == "webapp"]


def clear_blocked_items() -> None:
    """Completely clear the list of blocked items and save to disk."""
    global blocked_items
    blocked_items = []
    save_blocked_items()
    print("[INFO] Lista elementi bloccati svuotata")


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "blocked_items",
    "save_blocked_items",
    "load_blocked_items",
    "add_blocked_item",
    "remove_blocked_item",
    "get_blocked_items",
    "get_blocked_apps",
    "get_blocked_webapps",
    "clear_blocked_items",
]
