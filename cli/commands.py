"""
cli/commands.py
Comandi CLI per Modalità Studio.
"""

import sys
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from core.storage import (
    blocked_items,
    load_blocked_items,
    save_blocked_items,
    add_blocked_item,
    remove_blocked_item,
    get_blocked_items,
    get_blocked_apps,
    get_blocked_webapps
)
from core.blocker import (
    is_blocking_active,
    set_blocking_active,
    get_blocking_stats,
    get_blocking_stats
)

console = Console()


# ============================================================================
# COMANDI
# ============================================================================

def cmd_status():
    """Mostra lo stato corrente della modalità studio."""
    stats = get_blocking_stats()

    status_emoji = "🔒" if stats['blocking_active'] else "🔓"
    status_text = "ATTIVO" if stats['blocking_active'] else "DISATTIVO"
    status_color = "green" if stats['blocking_active'] else "red"

    console.print()
    console.print(Panel(
        f"[bold {status_color}]{status_emoji} Blocco {status_text}[/]\n\n"
        f"Elementi bloccati: [cyan]{stats['blocked_items_count']}[/]\n"
        f"Intervallo controllo: [yellow]{stats['blocking_interval']}s[/]",
        title="📊 Stato Modalità Studio",
        border_style="blue",
        box=box.ROUNDED
    ))


def cmd_list():
    """Lista tutti gli elementi bloccati."""
    items = get_blocked_items()

    if not items:
        console.print("\n[yellow]ℹ️  Nessun elemento bloccato[/]\n")
        return

    # Crea tabella
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


def cmd_add(name: str, item_type: str):
    """
    Aggiunge un elemento alla lista bloccati.

    Args:
        name: Nome app o URL webapp
        item_type: 'app' o 'webapp'
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
    Rimuove un elemento dalla lista.

    Args:
        identifier: Indice (numero) o nome esatto dell'elemento
    """
    items = get_blocked_items()

    if not items:
        console.print("\n[yellow]ℹ️  Lista vuota, niente da rimuovere[/]\n")
        return

    # Prova come indice
    try:
        index = int(identifier) - 1  # L'utente vede indici 1-based
        if 0 <= index < len(items):
            item_name = items[index]["name"]
            if remove_blocked_item(index):
                console.print(f"\n[green]✅ '{item_name}' rimosso![/]\n")
                return
    except ValueError:
        pass

    # Prova come nome
    for idx, item in enumerate(items):
        if item["name"] == identifier:
            if remove_blocked_item(idx):
                console.print(f"\n[green]✅ '{identifier}' rimosso![/]\n")
                return

    console.print(f"\n[red]❌ Elemento '{identifier}' non trovato[/]\n")


def cmd_start():
    """Attiva il blocco."""
    if is_blocking_active():
        console.print("\n[yellow]ℹ️  Il blocco è già attivo[/]\n")
        return

    set_blocking_active(True)
    console.print("\n[green]🔒 Blocco ATTIVATO[/]\n")


def cmd_stop():
    """Disattiva il blocco."""
    if not is_blocking_active():
        console.print("\n[yellow]ℹ️  Il blocco è già disattivo[/]\n")
        return

    set_blocking_active(False)
    console.print("\n[red]🔓 Blocco DISATTIVATO[/]\n")


def cmd_toggle():
    """Inverti lo stato del blocco."""
    from core.blocker import toggle_blocking

    new_state = toggle_blocking()

    if new_state:
        console.print("\n[green]🔒 Blocco ATTIVATO[/]\n")
    else:
        console.print("\n[red]🔓 Blocco DISATTIVATO[/]\n")


def cmd_clear():
    """Rimuove tutti gli elementi dalla lista."""
    if not get_blocked_items():
        console.print("\n[yellow]ℹ️  Lista già vuota[/]\n")
        return

    from rich.prompt import Confirm

    if Confirm.ask("\n[red]⚠️  Rimuovere TUTTI gli elementi?[/]"):
        from core.storage import clear_blocked_items
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
    'cmd_add',
    'cmd_remove',
    'cmd_start',
    'cmd_stop',
    'cmd_toggle',
    'cmd_clear',
]
