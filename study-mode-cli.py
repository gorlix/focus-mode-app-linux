#!/usr/bin/env python3
"""
study-mode-cli.py
Interfaccia command-line per Modalità Studio.

Uso:
    study-mode-cli status               Mostra stato
    study-mode-cli list                 Lista elementi
    study-mode-cli add <nome> <tipo>    Aggiungi elemento
    study-mode-cli remove <id>          Rimuovi elemento
    study-mode-cli start                Attiva blocco
    study-mode-cli stop                 Disattiva blocco
    study-mode-cli toggle               Inverti stato
    study-mode-cli clear                Svuota lista
"""

import sys
import argparse
from rich.console import Console

from config import load_config
from core.storage import load_blocked_items
from cli.commands import (
    cmd_status,
    cmd_list,
    cmd_add,
    cmd_remove,
    cmd_start,
    cmd_stop,
    cmd_toggle,
    cmd_clear
)

console = Console()


def print_help():
    """Stampa help personalizzato."""
    console.print("""
[bold cyan]🎯 Modalità Studio - CLI[/]

[bold]Comandi:[/]
  [green]status[/]              Mostra stato corrente
  [green]list[/]                Lista tutti gli elementi bloccati
  [green]add[/] <nome> <tipo>   Aggiungi elemento (tipo: app/webapp)
  [green]remove[/] <id|nome>    Rimuovi elemento per indice o nome
  [green]start[/]               Attiva il blocco
  [green]stop[/]                Disattiva il blocco
  [green]toggle[/]              Inverti stato blocco
  [green]clear[/]               Svuota lista elementi

[bold]Esempi:[/]
  study-mode-cli add firefox app
  study-mode-cli add web.whatsapp.com webapp
  study-mode-cli remove 1
  study-mode-cli start
  study-mode-cli status

[dim]Nota: Per l'interfaccia grafica usa: python main.py[/]
    """)


def main():
    """Entry point CLI."""
    # Carica configurazione
    load_config()
    load_blocked_items()

    # Parse argomenti
    parser = argparse.ArgumentParser(
        description="Modalità Studio - CLI",
        add_help=False
    )
    parser.add_argument('command', nargs='?', help='Comando da eseguire')
    parser.add_argument('args', nargs='*', help='Argomenti del comando')
    parser.add_argument('-h', '--help', action='store_true', help='Mostra help')

    args = parser.parse_args()

    # Help
    if args.help or not args.command:
        print_help()
        sys.exit(0)

    # Esegui comando
    command = args.command.lower()

    try:
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

        elif command == 'start':
            cmd_start()

        elif command == 'stop':
            cmd_stop()

        elif command == 'toggle':
            cmd_toggle()

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
