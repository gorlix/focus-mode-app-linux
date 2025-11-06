"""
core/blocker.py
Logica di blocco dei processi (app native e webapp).
Gestisce il monitoraggio continuo e la terminazione dei processi bloccati.
Integra session restore per tracciare app killate.
Integra focus lock per impedire disattivazione prematura.
"""

import os
import time
import psutil
from typing import Set, Tuple

from config import BLOCKING_INTERVAL, BLOCKING_ACTIVE_ON_STARTUP, AUTO_RESTORE_ENABLED

blocking_active = BLOCKING_ACTIVE_ON_STARTUP

_killed_pids: Set[int] = set()

_restore_enabled_this_session = AUTO_RESTORE_ENABLED


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
        _killed_pids.clear()
    else:
        print("[INFO] Blocco DISATTIVATO")


def can_disable_blocking() -> Tuple[bool, str]:
    """
    Verifica se è possibile disattivare il blocco.
    Controlla focus lock prima di permettere disattivazione.

    Returns:
        Tuple[bool, str]: (can_disable, reason)
    """
    if not blocking_active:
        return (True, "Blocco già disattivo")

    try:
        from core.focus_lock import focus_lock

        if focus_lock.is_locked():
            info = focus_lock.get_lock_info()
            return (False, f"Focus Lock attivo - {info['remaining_time']} rimanenti")
    except ImportError:
        pass

    return (True, "OK")


def toggle_blocking() -> bool:
    """
    Inverte lo stato del blocco (attivo <-> disattivato).
    Gestisce auto-restore alla disattivazione.
    Controlla focus lock prima di disattivare.

    Returns:
        bool: Nuovo stato del blocco
    """
    global blocking_active

    old_state = blocking_active

    if old_state:
        can_disable, reason = can_disable_blocking()
        if not can_disable:
            print(f"[WARNING] Cannot disable blocking: {reason}")
            return blocking_active

    blocking_active = not blocking_active

    if blocking_active:
        print("[INFO] Blocco ATTIVATO")
        _killed_pids.clear()
    else:
        print("[INFO] Blocco DISATTIVATO")

        if old_state and not blocking_active:
            _handle_auto_restore()

    return blocking_active


def _handle_auto_restore() -> None:
    """
    Gestisce il ripristino automatico app killate quando blocco viene disattivato.
    Eseguito solo se auto_restore è abilitato.
    """
    if not _restore_enabled_this_session:
        print("[INFO] Auto-restore disabilitato per questa sessione")
        return

    try:
        from core.session import session_tracker
        from core.restore import restore_all_apps
        from core.notifications import notify_restore_complete

        killed_apps = session_tracker.get_killed_apps()

        if not killed_apps:
            return

        print(f"[INFO] Avvio auto-restore: {len(killed_apps)} app")

        restored_count = restore_all_apps()

        notify_restore_complete(restored_count)

    except Exception as e:
        print(f"[ERROR] Errore durante auto-restore: {e}")


def set_restore_enabled(enabled: bool) -> None:
    """
    Abilita o disabilita il restore automatico per questa sessione.

    Args:
        enabled: True per abilitare, False per disabilitare
    """
    global _restore_enabled_this_session
    _restore_enabled_this_session = enabled

    status = "abilitato" if enabled else "disabilitato"
    print(f"[INFO] Auto-restore {status} per questa sessione")


def is_restore_enabled() -> bool:
    """
    Ritorna lo stato del restore automatico.

    Returns:
        bool: True se auto-restore è abilitato
    """
    return _restore_enabled_this_session


# ============================================================================
# BLOCCO PROCESSI
# ============================================================================

def kill_blocked_apps() -> int:
    """
    Blocca tutte le app native nella lista.
    Traccia app killate se nella restore list.

    Returns:
        int: Numero di processi killati
    """
    if not blocking_active:
        return 0

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

                    if app_name in proc_name and proc_pid != current_pid:

                        if proc_pid not in _killed_pids:
                            print(f"[INFO] Killing app: {app_name} (PID {proc_pid})")
                            _killed_pids.add(proc_pid)

                            try:
                                from core.session import session_tracker
                                app_state = session_tracker.capture_app_state(proc)
                                if app_state:
                                    session_tracker.add_killed_app(app_name, app_state)
                            except Exception as e:
                                print(f"[WARNING] Session capture error: {e}")

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
    Traccia webapp killate se nella restore list.

    Returns:
        int: Numero di processi killati
    """
    if not blocking_active:
        return 0

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

                    cmdline_str = ' '.join(cmdline_list)
                    proc_pid = proc.info['pid']

                    if webapp_string in cmdline_str:

                        if proc_pid not in _killed_pids:
                            print(f"[INFO] Killing webapp: {webapp_string} (PID {proc_pid})")
                            _killed_pids.add(proc_pid)

                            try:
                                from core.session import session_tracker
                                app_state = session_tracker.capture_app_state(proc)
                                if app_state:
                                    session_tracker.add_killed_app(webapp_string, app_state)
                            except Exception as e:
                                print(f"[WARNING] Session capture error: {e}")

                        proc.kill()
                        killed_count += 1
                        break

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

    while True:
        try:
            if blocking_active:
                killed = kill_all_blocked_items()

                if killed > 0:
                    print(f"[DEBUG] Processi killati in questo ciclo: {killed}")

            time.sleep(BLOCKING_INTERVAL)

        except KeyboardInterrupt:
            print("\n[INFO] Loop di blocco interrotto dall'utente")
            break

        except Exception as e:
            print(f"[ERROR] Errore nel loop di blocco: {e}")
            time.sleep(BLOCKING_INTERVAL)


def cleanup_killed_pids() -> None:
    """
    Pulisce il set dei PID tracciati.
    Utile per reset e cleanup della memoria.
    """
    global _killed_pids
    _killed_pids.clear()
    print("[DEBUG] Set PID killati resettato")


# ============================================================================
# STATISTICHE
# ============================================================================

def get_blocking_stats() -> dict:
    """
    Ritorna statistiche sul blocco, session restore e focus lock.

    Returns:
        dict: Dizionario con statistiche di blocco, restore e lock
    """
    from core.storage import blocked_items

    try:
        from core.session import session_tracker
        killed_apps_count = len(session_tracker.get_killed_apps())
        restore_list_count = len(session_tracker.restore_list)
    except:
        killed_apps_count = 0
        restore_list_count = 0

    try:
        from core.focus_lock import focus_lock
        lock_info = focus_lock.get_lock_info()
    except:
        lock_info = {"locked": False}

    return {
        "blocking_active": blocking_active,
        "blocked_items_count": len(blocked_items),
        "killed_pids_tracked": len(_killed_pids),
        "blocking_interval": BLOCKING_INTERVAL,
        "auto_restore_enabled": _restore_enabled_this_session,
        "apps_to_restore_count": restore_list_count,
        "killed_apps_in_session": killed_apps_count,
        "focus_lock": lock_info,
    }


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    'blocking_active',
    'is_blocking_active',
    'set_blocking_active',
    'toggle_blocking',
    'can_disable_blocking',
    'set_restore_enabled',
    'is_restore_enabled',
    'kill_blocked_apps',
    'kill_blocked_webapps',
    'kill_all_blocked_items',
    'start_blocking_loop',
    'get_blocking_stats',
    'cleanup_killed_pids',
]
