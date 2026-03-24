"""
cli/commands.py
Comandi CLI per Focus Mode App.
Interfaccia command-line per gestire app bloccate, sessioni, restore e focus lock.
Supporta sia timer countdown che target time per il focus lock.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from focus_mode_app.core.storage import (
    add_blocked_item,
    remove_blocked_item,
    get_blocked_items
)
from focus_mode_app.core.blocker import (
    is_blocking_active,
    set_blocking_active,
    toggle_blocking,
    set_restore_enabled,
    is_restore_enabled,
    get_blocking_stats
)

console = Console()


# ============================================================================
# COMANDI STATUS E INFORMAZIONI
# ============================================================================

def cmd_status():
    """
    Mostra lo stato corrente del blocco, sessione e focus lock.
    Include informazioni su blocco attivo, elementi bloccati, app da ripristinare e timer.
    """
    stats = get_blocking_stats()

    status_emoji = "🔒" if stats['blocking_active'] else "🔓"
    status_text = "ATTIVO" if stats['blocking_active'] else "DISATTIVO"
    status_color = "green" if stats['blocking_active'] else "red"

    restore_info = f"Apps da ripristinare: [cyan]{stats['apps_to_restore_count']}[/]"
    restore_status = f"Auto-restore: [bold]{'ABILITATO' if stats['auto_restore_enabled'] else 'DISABILITATO'}[/]"

    lock_info = stats.get('focus_lock', {})
    if lock_info.get('locked'):
        lock_status = f"🔒 Focus Lock: [red]ATTIVO[/] - {lock_info['remaining_time']} rimanenti"
    else:
        lock_status = "Focus Lock: [green]Nessun lock attivo[/]"

    console.print()
    console.print(Panel(
        f"[bold {status_color}]{status_emoji} Blocco {status_text}[/]\n\n"
        f"Elementi bloccati: [cyan]{stats['blocked_items_count']}[/]\n"
        f"App killate in sessione: [yellow]{stats['killed_apps_in_session']}[/]\n"
        f"{restore_info}\n"
        f"{restore_status}\n"
        f"{lock_status}\n"
        f"Intervallo controllo: [dim]{stats['blocking_interval']}s[/]",
        title="📊 Stato Focus Mode App",
        border_style="blue",
        box=box.ROUNDED
    ))


def cmd_list():
    """
    Lista tutti gli elementi bloccati (app native e webapp).
    Visualizza tipo e nome di ogni elemento con indice numerico.
    """
    items = get_blocked_items()

    if not items:
        console.print("\n[yellow]ℹ️  Nessun elemento bloccato[/]\n")
        return

    table = Table(title="🚫 Elementi Bloccati", box=box.ROUNDED)
    table.add_column("#", style="dim", width=4)
    table.add_column("Tipo", style="cyan", width=10)
    table.add_column("Nome/URL", style="white")

    for idx, item in enumerate(items, 1):
        emoji = "📱" if item["type"] == "app" else "🌐"
        tipo = f"{emoji} App" if item["type"] == "app" else f"{emoji} Webapp"
        table.add_row(str(idx), tipo, item["name"])

    console.print()
    console.print(table)
    console.print()


def cmd_list_restore():
    """
    Lista tutte le app configurate per il restore automatico.
    Mostra quali app verranno ripristinate quando il blocco viene disattivato.
    """
    try:
        from focus_mode_app.core.session import session_tracker

        restore_list = session_tracker.restore_list

        if not restore_list:
            console.print("\n[yellow]ℹ️  Nessuna app configurata per restore[/]\n")
            return

        table = Table(title="♻️ App Configurate per Auto-Restore", box=box.ROUNDED)
        table.add_column("#", style="dim", width=4)
        table.add_column("App", style="cyan")

        for idx, app_name in enumerate(restore_list.keys(), 1):
            table.add_row(str(idx), f"♻️ {app_name}")

        console.print()
        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"\n[red]❌ Errore: {e}[/]\n")


# ============================================================================
# COMANDI GESTIONE ELEMENTI BLOCCATI
# ============================================================================

def cmd_add(name: str, item_type: str):
    """
    Aggiunge un elemento alla lista bloccati.

    Args:
        name: Nome app o URL webapp
        item_type: Tipo elemento ('app' o 'webapp')
    """
    if item_type not in ['app', 'webapp']:
        console.print(f"\n[red]❌ Tipo non valido: {item_type}[/]")
        console.print("[yellow]Usa 'app' o 'webapp'[/]\n")
        return

    if add_blocked_item(name, item_type):
        emoji = "📱" if item_type == "app" else "🌐"
        console.print(f"\n[green]✅ {emoji} '{name}' aggiunto alla lista![/]\n")
    else:
        console.print(f"\n[yellow]⚠️  '{name}' già presente nella lista[/]\n")


def cmd_remove(identifier: str):
    """
    Rimuove un elemento dalla lista bloccati.
    Accetta indice numerico (1-based) o nome esatto dell'elemento.

    Args:
        identifier: Indice (numero) o nome esatto dell'elemento
    """
    items = get_blocked_items()

    if not items:
        console.print("\n[yellow]ℹ️  Lista vuota, niente da rimuovere[/]\n")
        return

    try:
        index = int(identifier) - 1
        if 0 <= index < len(items):
            item_name = items[index]["name"]
            if remove_blocked_item(index):
                console.print(f"\n[green]✅ '{item_name}' rimosso![/]\n")
                return
    except ValueError:
        pass

    for idx, item in enumerate(items):
        if item["name"] == identifier:
            if remove_blocked_item(idx):
                console.print(f"\n[green]✅ '{identifier}' rimosso![/]\n")
                return

    console.print(f"\n[red]❌ Elemento '{identifier}' non trovato[/]\n")


# ============================================================================
# COMANDI GESTIONE BLOCCO
# ============================================================================

def cmd_start():
    """Attiva il blocco dei processi."""
    if is_blocking_active():
        console.print("\n[yellow]ℹ️  Il blocco è già attivo[/]\n")
        return

    set_blocking_active(True)
    console.print("\n[green]🔒 Blocco ATTIVATO - App verranno bloccate[/]\n")


def cmd_stop():
    """
    Disattiva il blocco dei processi.
    Controlla focus lock prima di permettere disattivazione.
    """
    if not is_blocking_active():
        console.print("\n[yellow]ℹ️  Il blocco è già disattivo[/]\n")
        return

    from focus_mode_app.core.blocker import can_disable_blocking

    can_disable, reason = can_disable_blocking()
    if not can_disable:
        console.print(f"\n[red]❌ {reason}[/]\n")
        return

    set_blocking_active(False)
    console.print("\n[red]🔓 Blocco DISATTIVATO[/]\n")

    try:
        from focus_mode_app.core.session import session_tracker

        killed_apps = session_tracker.get_killed_apps()

        if killed_apps:
            restored = len(killed_apps)
            console.print(f"[green]✅ Auto-restore completato: {restored} app ripristinate[/]\n")
    except Exception as e:
        console.print(f"[yellow]⚠️  Errore durante auto-restore: {e}[/]\n")


def cmd_toggle():
    """
    Inverti lo stato del blocco (attivo <-> disattivato).
    Gestisce anche il restore automatico alla disattivazione.
    Controlla focus lock prima di disattivare.
    """
    if is_blocking_active():
        from focus_mode_app.core.blocker import can_disable_blocking

        can_disable, reason = can_disable_blocking()
        if not can_disable:
            console.print(f"\n[red]❌ {reason}[/]\n")
            return

    new_state = toggle_blocking()

    if new_state:
        console.print("\n[green]🔒 Blocco ATTIVATO[/]\n")
    else:
        console.print("\n[red]🔓 Blocco DISATTIVATO[/]\n")


# ============================================================================
# COMANDI GESTIONE RESTORE
# ============================================================================

def cmd_add_restore(app_name: str):
    """
    Aggiunge un'app alla lista di restore automatico.
    L'app verrà ripristinata quando il blocco viene disattivato.

    Args:
        app_name: Nome app da aggiungere a restore
    """
    try:
        from focus_mode_app.core.session import session_tracker

        session_tracker.add_to_restore(app_name)
        console.print(f"\n[green]✅ '{app_name}' aggiunto a auto-restore![/]\n")
    except Exception as e:
        console.print(f"\n[red]❌ Errore: {e}[/]\n")


def cmd_remove_restore(app_name: str):
    """
    Rimuove un'app dalla lista di restore automatico.

    Args:
        app_name: Nome app da rimuovere da restore
    """
    try:
        from focus_mode_app.core.session import session_tracker

        session_tracker.remove_from_restore(app_name)
        console.print(f"\n[green]✅ '{app_name}' rimosso da auto-restore![/]\n")
    except Exception as e:
        console.print(f"\n[red]❌ Errore: {e}[/]\n")


def cmd_restore():
    """
    Ripristina manualmente tutte le app killate nella sessione corrente.
    Utile per forzare il restore senza aspettare la disattivazione del blocco.
    """
    try:
        from focus_mode_app.core.restore import restore_all_apps
        from focus_mode_app.core.session import session_tracker

        apps = session_tracker.get_killed_apps()

        if not apps:
            console.print("\n[yellow]ℹ️  Nessuna app da ripristinare[/]\n")
            return

        console.print(f"\n[cyan]♻️  Ripristino {len(apps)} app...[/]")
        restored = restore_all_apps()
        console.print(f"[green]✅ Ripristinate {restored} app![/]\n")

    except Exception as e:
        console.print(f"\n[red]❌ Errore: {e}[/]\n")


def cmd_toggle_restore():
    """
    Abilita o disabilita il restore automatico per la sessione corrente.
    Permette di controllare se le app verranno ripristinate automaticamente.
    """
    current_state = is_restore_enabled()
    new_state = not current_state

    set_restore_enabled(new_state)

    status = "ABILITATO" if new_state else "DISABILITATO"
    console.print(f"\n[cyan]Auto-restore {status}[/]\n")


# ============================================================================
# COMANDI GESTIONE FOCUS LOCK
# ============================================================================

def cmd_set_timer(minutes: int):
    """
    Attiva focus lock con timer countdown.

    Args:
        minutes: Durata timer in minuti
    """
    try:
        from focus_mode_app.core.focus_lock import focus_lock

        if focus_lock.set_timer_lock(minutes):
            console.print(f"\n[green]🔒 Focus Lock attivato: {minutes} minuti[/]\n")

            if not is_blocking_active():
                cmd_start()
        else:
            console.print("\n[red]❌ Errore attivazione timer[/]\n")

    except Exception as e:
        console.print(f"\n[red]❌ Errore: {e}[/]\n")


def cmd_set_target_time(hour: int, minute: int):
    """
    Attiva focus lock fino a orario target.
    Supporta orario di domani se l'ora è già passata.

    Args:
        hour: Ora target (0-23)
        minute: Minuto target (0-59)
    """
    try:
        from focus_mode_app.core.focus_lock import focus_lock

        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            console.print("\n[red]❌ Ora non valida (HH: 0-23, MM: 0-59)[/]\n")
            return

        if focus_lock.set_target_time_lock(hour, minute):
            console.print(f"\n[green]🔒 Target Time Lock attivato: fino alle {hour:02d}:{minute:02d}[/]\n")

            if not is_blocking_active():
                cmd_start()
        else:
            console.print("\n[red]❌ Errore attivazione target time[/]\n")

    except Exception as e:
        console.print(f"\n[red]❌ Errore: {e}[/]\n")


def cmd_lock_status():
    """Mostra stato focus lock con countdown e dettagli."""
    try:
        from focus_mode_app.core.focus_lock import focus_lock

        info = focus_lock.get_lock_info()

        if info['locked']:
            mode = "⏲️  TIMER" if info['mode'] == "timer" else "🕐 TARGET TIME"

            console.print()
            console.print(Panel(
                f"[red]🔒 FOCUS LOCK ATTIVO[/]\n\n"
                f"Modalità: [cyan]{mode}[/]\n"
                f"Tempo rimanente: [yellow]{info['remaining_time']}[/]\n"
                f"Scadenza: [cyan]{info['end_time']}[/]\n"
                f"Progress: [cyan]{info['progress_percentage']:.1f}%[/]",
                title="Focus Lock Status",
                border_style="red",
                box=box.ROUNDED
            ))
            console.print()
        else:
            console.print("\n[green]✅ Nessun lock attivo[/]\n")

    except ImportError:
        console.print("\n[yellow]⚠️  Focus lock non disponibile[/]\n")
    except Exception as e:
        console.print(f"\n[red]❌ Errore: {e}[/]\n")


def cmd_clear_lock():
    """
    Rimuove focus lock manualmente (force unlock).
    Richiede conferma dell'utente.
    """
    try:
        from focus_mode_app.core.focus_lock import focus_lock
        from rich.prompt import Confirm

        if not focus_lock.is_locked():
            console.print("\n[yellow]ℹ️  Nessun lock attivo[/]\n")
            return

        if Confirm.ask("\n[red]⚠️  Sbloccare manualmente il focus lock?[/]"):
            focus_lock.force_unlock()
            console.print("\n[green]✅ Focus lock rimosso![/]\n")
        else:
            console.print("\n[yellow]Operazione annullata[/]\n")

    except Exception as e:
        console.print(f"\n[red]❌ Errore: {e}[/]\n")


# ============================================================================
# COMANDI GESTIONE LISTA
# ============================================================================

def cmd_clear():
    """
    Rimuove tutti gli elementi dalla lista bloccati.
    Richiede conferma dell'utente prima di procedere.
    """
    if not get_blocked_items():
        console.print("\n[yellow]ℹ️  Lista già vuota[/]\n")
        return

    from rich.prompt import Confirm

    if Confirm.ask("\n[red]⚠️  Rimuovere TUTTI gli elementi?[/]"):
        from focus_mode_app.core.storage import clear_blocked_items
        clear_blocked_items()
        console.print("\n[green]✅ Lista svuotata![/]\n")
    else:
        console.print("\n[yellow]Operazione annullata[/]\n")


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    'cmd_status',
    'cmd_list',
    'cmd_list_restore',
    'cmd_add',
    'cmd_remove',
    'cmd_start',
    'cmd_stop',
    'cmd_toggle',
    'cmd_add_restore',
    'cmd_remove_restore',
    'cmd_restore',
    'cmd_toggle_restore',
    'cmd_set_timer',
    'cmd_set_target_time',
    'cmd_lock_status',
    'cmd_clear_lock',
    'cmd_clear',
]
