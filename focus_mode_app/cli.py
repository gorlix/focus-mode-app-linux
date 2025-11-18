#!/usr/bin/env python3
"""
cli.py
Interfaccia command-line per Focus Mode App.

Supporta gestione blocco, restore e focus lock (timer/target time).

Uso:
    study-mode-cli status                  Mostra stato
    study-mode-cli list                    Lista elementi
    study-mode-cli add <nome> <tipo>       Aggiungi elemento
    study-mode-cli remove <id>             Rimuovi elemento
    study-mode-cli start                   Attiva blocco
    study-mode-cli stop                    Disattiva blocco
    study-mode-cli toggle                  Inverti stato

    study-mode-cli list-restore            Lista app per restore
    study-mode-cli add-restore <app>       Aggiungi app a restore
    study-mode-cli remove-restore <app>    Rimuovi app da restore
    study-mode-cli restore                 Ripristina app manualmente
    study-mode-cli toggle-restore          Toggle auto-restore

    study-mode-cli set-timer <minuti>      Attiva timer lock
    study-mode-cli set-target-time <HH> <MM>  Attiva target time lock
    study-mode-cli lock-status             Mostra stato focus lock
    study-mode-cli clear-lock              Sblocca manualmente

    study-mode-cli clear                   Svuota lista elementi
"""

import sys
import argparse
from rich.console import Console

from focus_mode_app.config import load_config
from focus_mode_app.core.storage import load_blocked_items
from focus_mode_app.cli.commands import (
    cmd_status,
    cmd_list,
    cmd_list_restore,
    cmd_add,
    cmd_remove,
    cmd_start,
    cmd_stop,
    cmd_toggle,
    cmd_add_restore,
    cmd_remove_restore,
    cmd_restore,
    cmd_toggle_restore,
    cmd_set_timer,
    cmd_set_target_time,
    cmd_lock_status,
    cmd_clear_lock,
    cmd_clear
)

console = Console()


def print_help():
    """Stampa help personalizzato."""
    console.print("""
[bold cyan]🎯 Focus Mode App - CLI[/]

[bold]📋 COMANDI BASE:[/]
  [green]status[/]              Mostra stato corrente blocco
  [green]list[/]                Lista tutti gli elementi bloccati
  [green]add[/] <nome> <tipo>   Aggiungi elemento (tipo: app/webapp)
  [green]remove[/] <id|nome>    Rimuovi elemento per indice o nome
  [green]clear[/]               Svuota lista elementi

[bold]🔒 COMANDI BLOCCO:[/]
  [green]start[/]               Attiva il blocco
  [green]stop[/]                Disattiva il blocco (se possibile)
  [green]toggle[/]              Inverti stato blocco

[bold]♻️  COMANDI RESTORE:[/]
  [green]list-restore[/]        Lista app configurate per restore
  [green]add-restore[/] <app>   Aggiungi app a ripristino automatico
  [green]remove-restore[/] <app>  Rimuovi app da ripristino
  [green]restore[/]             Ripristina manualmente le app
  [green]toggle-restore[/]      Abilita/disabilita auto-restore

[bold]⏱️  COMANDI FOCUS LOCK:[/]
  [green]set-timer[/] <min>     Attiva timer lock (es: set-timer 25)
  [green]set-target-time[/] <HH> <MM>  Lock fino a ora (es: set-target-time 14 30)
  [green]lock-status[/]         Mostra countdown focus lock
  [green]clear-lock[/]          Sblocca manualmente (force unlock)

[bold]📚 ESEMPI:[/]
  study-mode-cli add firefox app
  study-mode-cli add web.whatsapp.com webapp
  study-mode-cli list
  study-mode-cli remove 1
  study-mode-cli start
  study-mode-cli status
  study-mode-cli add-restore firefox
  study-mode-cli set-timer 25
  study-mode-cli set-target-time 14 30
  study-mode-cli lock-status

[dim]💡 Per l'interfaccia grafica usa: python main.py[/]
    """)


def main():
    """Entry point CLI."""
    load_config()
    load_blocked_items()

    parser = argparse.ArgumentParser(
        description="Focus Mode App - CLI",
        add_help=False
    )
    parser.add_argument('command', nargs='?', help='Comando da eseguire')
    parser.add_argument('args', nargs='*', help='Argomenti del comando')
    parser.add_argument('-h', '--help', action='store_true', help='Mostra help')

    args = parser.parse_args()

    if args.help or not args.command:
        print_help()
        sys.exit(0)

    command = args.command.lower()

    try:
        # ====================================================================
        # COMANDI BASE
        # ====================================================================

        if command == 'status':
            cmd_status()

        elif command == 'list' or command == 'ls':
            cmd_list()

        elif command == 'add':
            if len(args.args) < 2:
                console.print("\n[red]❌ Uso: study-mode-cli add <nome> <tipo>[/]")
                console.print("[yellow]Esempio: study-mode-cli add firefox app[/]\n")
                sys.exit(1)

            name = args.args[0]
            item_type = args.args[1].lower()
            cmd_add(name, item_type)

        elif command == 'remove' or command == 'rm':
            if len(args.args) < 1:
                console.print("\n[red]❌ Uso: study-mode-cli remove <id|nome>[/]\n")
                sys.exit(1)

            identifier = args.args[0]
            cmd_remove(identifier)

        # ====================================================================
        # COMANDI BLOCCO
        # ====================================================================

        elif command == 'start':
            cmd_start()

        elif command == 'stop':
            cmd_stop()

        elif command == 'toggle':
            cmd_toggle()

        # ====================================================================
        # COMANDI RESTORE
        # ====================================================================

        elif command == 'list-restore':
            cmd_list_restore()

        elif command == 'add-restore':
            if len(args.args) < 1:
                console.print("\n[red]❌ Uso: study-mode-cli add-restore <app>[/]")
                console.print("[yellow]Esempio: study-mode-cli add-restore firefox[/]\n")
                sys.exit(1)

            app_name = args.args[0]
            cmd_add_restore(app_name)

        elif command == 'remove-restore':
            if len(args.args) < 1:
                console.print("\n[red]❌ Uso: study-mode-cli remove-restore <app>[/]\n")
                sys.exit(1)

            app_name = args.args[0]
            cmd_remove_restore(app_name)

        elif command == 'restore':
            cmd_restore()

        elif command == 'toggle-restore':
            cmd_toggle_restore()

        # ====================================================================
        # COMANDI FOCUS LOCK
        # ====================================================================

        elif command == 'set-timer':
            if len(args.args) < 1:
                console.print("\n[red]❌ Uso: study-mode-cli set-timer <minuti>[/]")
                console.print("[yellow]Esempio: study-mode-cli set-timer 25[/]\n")
                sys.exit(1)

            try:
                minutes = int(args.args[0])
                cmd_set_timer(minutes)
            except ValueError:
                console.print("\n[red]❌ Minuti deve essere un numero[/]\n")
                sys.exit(1)

        elif command == 'set-target-time':
            if len(args.args) < 2:
                console.print("\n[red]❌ Uso: study-mode-cli set-target-time <HH> <MM>[/]")
                console.print("[yellow]Esempio: study-mode-cli set-target-time 14 30[/]\n")
                sys.exit(1)

            try:
                hour = int(args.args[0])
                minute = int(args.args[1])
                cmd_set_target_time(hour, minute)
            except ValueError:
                console.print("\n[red]❌ Ora e minuti devono essere numeri[/]\n")
                sys.exit(1)

        elif command == 'lock-status':
            cmd_lock_status()

        elif command == 'clear-lock':
            cmd_clear_lock()

        # ====================================================================
        # COMANDI UTILITY
        # ====================================================================

        elif command == 'clear':
            cmd_clear()

        else:
            console.print(f"\n[red]❌ Comando sconosciuto: {command}[/]\n")
            print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Operazione annullata[/]\n")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]❌ Errore: {e}[/]\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
