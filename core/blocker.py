"""
core/blocker.py
Logica di blocco dei processi (app native e webapp).
Gestisce il monitoraggio continuo e la terminazione dei processi bloccati.
"""

import os
import time
import psutil
from typing import Set

from config import BLOCKING_INTERVAL, BLOCKING_ACTIVE_ON_STARTUP

# NON importare blocked_items qui - causa problemi di riferimento
# from core.storage import blocked_items

# Stato globale del blocco (True = attivo, False = disattivato)
blocking_active = BLOCKING_ACTIVE_ON_STARTUP

# Set per tracciare i PID già killati (evita log ripetitivi)
_killed_pids: Set[int] = set()


# ============================================================================
# CONTROLLO STATO BLOCCO
# ============================================================================

def is_blocking_active() -> bool:
    """
    Ritorna lo stato corrente del blocco.
    
    Returns:
        bool: True se il blocco è attivo, False altrimenti
    """
    return blocking_active


def set_blocking_active(active: bool) -> None:
    """
    Imposta lo stato del blocco.
    
    Args:
        active: True per attivare, False per disattivare
    """
    global blocking_active
    blocking_active = active
    
    if active:
        print("[INFO] Blocco ATTIVATO")
        _killed_pids.clear()  # Reset dei PID tracciati
    else:
        print("[INFO] Blocco DISATTIVATO")


def toggle_blocking() -> bool:
    """
    Inverte lo stato del blocco (attivo <-> disattivato).
    
    Returns:
        bool: Nuovo stato del blocco
    """
    global blocking_active
    blocking_active = not blocking_active
    
    if blocking_active:
        print("[INFO] Blocco ATTIVATO")
        _killed_pids.clear()
    else:
        print("[INFO] Blocco DISATTIVATO")
    
    return blocking_active


# ============================================================================
# BLOCCO PROCESSI
# ============================================================================

def kill_blocked_apps() -> int:
    """
    Blocca tutte le app native nella lista.
    
    Returns:
        int: Numero di processi killati
    """
    if not blocking_active:
        return 0
    
    # Importa qui per avere sempre il riferimento aggiornato
    from core.storage import blocked_items
    
    if not blocked_items:
        return 0
    
    killed_count = 0
    current_pid = os.getpid()
    
    for item in blocked_items:
        if item["type"] != "app":
            continue
        
        app_name = item["name"].lower()
        
        try:
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    proc_name = proc.info['name'].lower()
                    proc_pid = proc.info['pid']
                    
                    # Controlla se il nome dell'app è nel nome del processo
                    if app_name in proc_name and proc_pid != current_pid:
                        # Evita log ripetitivi per lo stesso processo
                        if proc_pid not in _killed_pids:
                            print(f"[INFO] Killing app: {app_name} (PID {proc_pid})")
                            _killed_pids.add(proc_pid)
                        
                        proc.kill()
                        killed_count += 1
                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        
        except Exception as e:
            print(f"[ERROR] Errore durante blocco app '{app_name}': {e}")
    
    return killed_count


def kill_blocked_webapps() -> int:
    """
    Blocca tutte le webapp nella lista cercando nella command line dei processi.
    
    Returns:
        int: Numero di processi killati
    """
    if not blocking_active:
        return 0
    
    # Importa qui per avere sempre il riferimento aggiornato
    from core.storage import blocked_items
    
    if not blocked_items:
        return 0
    
    killed_count = 0
    
    for item in blocked_items:
        if item["type"] != "webapp":
            continue
        
        webapp_string = item["name"]
        
        try:
            for proc in psutil.process_iter(['cmdline', 'pid']):
                try:
                    cmdline_list = proc.info['cmdline']
                    if not cmdline_list:
                        continue
                    
                    # Concatena tutti gli argomenti in una stringa
                    cmdline_str = ' '.join(cmdline_list)
                    proc_pid = proc.info['pid']
                    
                    # Controlla se la stringa webapp è presente nella command line
                    if webapp_string in cmdline_str:
                        # Evita log ripetitivi
                        if proc_pid not in _killed_pids:
                            print(f"[INFO] Killing webapp: {webapp_string} (PID {proc_pid})")
                            _killed_pids.add(proc_pid)
                        
                        proc.kill()
                        killed_count += 1
                        break  # Una webapp per iterazione
                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        
        except Exception as e:
            print(f"[ERROR] Errore durante blocco webapp '{webapp_string}': {e}")
    
    return killed_count


def kill_all_blocked_items() -> int:
    """
    Blocca tutti gli elementi (app + webapp) nella lista.
    
    Returns:
        int: Numero totale di processi killati
    """
    if not blocking_active:
        return 0
    
    total_killed = 0
    total_killed += kill_blocked_apps()
    total_killed += kill_blocked_webapps()
    
    return total_killed


# ============================================================================
# LOOP DI MONITORAGGIO
# ============================================================================

def start_blocking_loop() -> None:
    """
    Avvia il loop infinito di monitoraggio e blocco processi.
    Questa funzione deve essere eseguita in un thread separato.
    
    Il loop continua finché l'applicazione è attiva.
    L'intervallo tra i controlli è definito in config.BLOCKING_INTERVAL.
    """
    print(f"[INFO] Loop di blocco avviato (intervallo: {BLOCKING_INTERVAL}s)")
    
    iteration = 0
    
    while True:
        try:
            iteration += 1
            
            # Esegui blocco solo se attivo
            if blocking_active:
                killed = kill_all_blocked_items()
                
                # Log solo se ha killato qualcosa (evita spam)
                if killed > 0:
                    print(f"[DEBUG] Processi killati in questo ciclo: {killed}")
            
            # Attendi prima del prossimo controllo
            time.sleep(BLOCKING_INTERVAL)
        
        except KeyboardInterrupt:
            print("\n[INFO] Loop di blocco interrotto dall'utente")
            break
        
        except Exception as e:
            print(f"[ERROR] Errore nel loop di blocco: {e}")
            time.sleep(BLOCKING_INTERVAL)  # Continua comunque


def cleanup_killed_pids() -> None:
    """
    Pulisce il set dei PID tracciati (utile per reset).
    """
    global _killed_pids
    _killed_pids.clear()
    print("[DEBUG] Set PID killati resettato")


# ============================================================================
# STATISTICHE (OPZIONALE)
# ============================================================================

def get_blocking_stats() -> dict:
    """
    Ritorna statistiche sul blocco.
    
    Returns:
        dict: Dizionario con statistiche
    """
    from core.storage import blocked_items
    
    return {
        "blocking_active": blocking_active,
        "blocked_items_count": len(blocked_items),
        "killed_pids_tracked": len(_killed_pids),
        "blocking_interval": BLOCKING_INTERVAL,
    }


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    'blocking_active',
    'is_blocking_active',
    'set_blocking_active',
    'toggle_blocking',
    'kill_blocked_apps',
    'kill_blocked_webapps',
    'kill_all_blocked_items',
    'start_blocking_loop',
    'get_blocking_stats',
]

