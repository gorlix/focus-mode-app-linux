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
    """
    Salva la lista degli elementi bloccati nel file JSON.
    
    Returns:
        bool: True se il salvataggio è riuscito, False altrimenti
    """
    data_file = get_data_file_path()
    
    try:
        with open(data_file, 'w', encoding='utf-8') as f:
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
    """
    Carica la lista degli elementi bloccati dal file JSON.
    Esegue migrazione automatica se rileva il vecchio formato.
    
    Returns:
        bool: True se il caricamento è riuscito, False altrimenti
    """
    global blocked_items
    data_file = get_data_file_path()
    
    if not data_file.exists():
        print(f"[INFO] File di configurazione non trovato: {data_file}")
        print(f"[INFO] Verrà creato automaticamente al primo salvataggio")
        blocked_items = []
        return True
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Controlla se è il vecchio formato (dict con "apps_native" e "webapp_elements")
        if isinstance(data, dict) and ("apps_native" in data or "webapp_elements" in data):
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
            print(f"[WARNING] Formato file non riconosciuto, inizializzazione lista vuota")
            blocked_items = []
        
        print(f"[INFO] Elementi bloccati caricati: {len(blocked_items)}")
        return True
    
    except json.JSONDecodeError as e:
        print(f"[ERROR] File JSON corrotto: {e}")
        print(f"[INFO] Inizializzazione lista vuota")
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
    """
    Converte il vecchio formato del file JSON al nuovo formato.
    
    Vecchio formato:
    {
        "apps_native": ["firefox", "telegram"],
        "webapp_elements": ["web.whatsapp.com"]
    }
    
    Nuovo formato:
    [
        {"name": "firefox", "type": "app"},
        {"name": "telegram", "type": "app"},
        {"name": "web.whatsapp.com", "type": "webapp"}
    ]
    
    Args:
        old_data: Dizionario con vecchio formato
        
    Returns:
        Lista nel nuovo formato
    """
    migrated_items = []
    
    # Migra app native
    for app_name in old_data.get("apps_native", []):
        migrated_items.append({
            "name": app_name,
            "type": "app"
        })
    
    # Migra webapp
    for webapp_url in old_data.get("webapp_elements", []):
        migrated_items.append({
            "name": webapp_url,
            "type": "webapp"
        })
    
    print(f"[INFO] Migrati {len(migrated_items)} elementi dal vecchio formato")
    return migrated_items


# ============================================================================
# FUNZIONI DI GESTIONE LISTA
# ============================================================================

def add_blocked_item(name: str, item_type: str) -> bool:
    """
    Aggiunge un elemento alla lista bloccati.
    
    Args:
        name: Nome dell'app o URL della webapp
        item_type: "app" o "webapp"
        
    Returns:
        bool: True se aggiunto, False se già presente o tipo non valido
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
    """
    Rimuove un elemento dalla lista bloccati per indice.
    
    Args:
        index: Indice dell'elemento da rimuovere
        
    Returns:
        bool: True se rimosso, False se indice non valido
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
    """
    Ritorna la lista completa degli elementi bloccati.
    
    Returns:
        Lista di dict con elementi bloccati
    """
    return blocked_items.copy()


def get_blocked_apps() -> List[str]:
    """
    Ritorna solo le app native bloccate.
    
    Returns:
        Lista di nomi app
    """
    return [item["name"] for item in blocked_items if item["type"] == "app"]


def get_blocked_webapps() -> List[str]:
    """
    Ritorna solo le webapp bloccate.
    
    Returns:
        Lista di URL/stringhe webapp
    """
    return [item["name"] for item in blocked_items if item["type"] == "webapp"]


def clear_blocked_items() -> None:
    """
    Svuota completamente la lista degli elementi bloccati.
    """
    global blocked_items
    blocked_items = []
    save_blocked_items()
    print("[INFO] Lista elementi bloccati svuotata")


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    'blocked_items',
    'save_blocked_items',
    'load_blocked_items',
    'add_blocked_item',
    'remove_blocked_item',
    'get_blocked_items',
    'get_blocked_apps',
    'get_blocked_webapps',
    'clear_blocked_items',
]

