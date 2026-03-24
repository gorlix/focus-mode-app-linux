#!/usr/bin/env python3
"""
cli.py
Command-line interface for the Focus Mode App.

Supports lock management, restoration, and focus lock (timer/target time).

Usage:
    study-mode-cli status                  Show current state
    study-mode-cli list                    List all elements
    study-mode-cli add <name> <type>       Add an element
    study-mode-cli remove <id>             Remove an element
    study-mode-cli start                   Activate the block
    study-mode-cli stop                    Deactivate the block
    study-mode-cli toggle                  Toggle blocking state

    study-mode-cli list-restore            List apps for auto-restore
    study-mode-cli add-restore <app>       Add an app to auto-restore
    study-mode-cli remove-restore <app>    Remove an app from auto-restore
    study-mode-cli restore                 Manually restore apps
    study-mode-cli toggle-restore          Toggle auto-restore functionality

    study-mode-cli set-timer <minutes>     Activate timer lock
    study-mode-cli set-target-time <HH> <MM>  Activate target time lock
    study-mode-cli lock-status             Show focus lock state
    study-mode-cli clear-lock              Manually unlock

    study-mode-cli clear                   Clear the blocklist
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
    cmd_clear,
)

console = Console()


def print_help() -> None:
    """Print the custom CLI help display to the console."""
    console.print("""
[bold cyan]🎯 Focus Mode App - CLI[/]

[bold]📋 BASIC COMMANDS:[/]
  [green]status[/]              Show current block status
  [green]list[/]                List all blocked elements
  [green]add[/] <name> <type>   Add element (type: app/webapp)
  [green]remove[/] <id|name>    Remove element by index or name
  [green]clear[/]               Clear the blocklist

[bold]🔒 BLOCK COMMANDS:[/]
  [green]start[/]               Activate the block
  [green]stop[/]                Deactivate the block (if allowed)
  [green]toggle[/]              Toggle block state

[bold]♻️  RESTORE COMMANDS:[/]
  [green]list-restore[/]        List apps configured for restore
  [green]add-restore[/] <app>   Add app to auto-restore
  [green]remove-restore[/] <app>  Remove app from auto-restore
  [green]restore[/]             Manually restore apps
  [green]toggle-restore[/]      Enable/disable auto-restore

[bold]⏱️  FOCUS LOCK COMMANDS:[/]
  [green]set-timer[/] <min>     Activate timer lock (e.g.: set-timer 25)
  [green]set-target-time[/] <HH> <MM>  Lock until time (e.g.: set-target-time 14 30)
  [green]lock-status[/]         Show focus lock countdown
  [green]clear-lock[/]          Manually unlock (force unlock)

[bold]📚 EXAMPLES:[/]
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

[dim]💡 For the graphical interface run: python main.py[/]
    """)


def main() -> None:
    """CLI application entry point.

    Loads configuration, parses command-line arguments, and delegates
    work to the respective CLI command functions.
    """
    load_config()
    load_blocked_items()

    parser = argparse.ArgumentParser(description="Focus Mode App - CLI", add_help=False)
    parser.add_argument("command", nargs="?", help="Command to execute")
    parser.add_argument("args", nargs="*", help="Command arguments")
    parser.add_argument("-h", "--help", action="store_true", help="Show help menu")

    args = parser.parse_args()

    if args.help or not args.command:
        print_help()
        sys.exit(0)

    command = args.command.lower()

    try:
        # ====================================================================
        # BASIC COMMANDS
        # ====================================================================

        if command == "status":
            cmd_status()

        elif command == "list" or command == "ls":
            cmd_list()

        elif command == "add":
            if len(args.args) < 2:
                console.print("\n[red]❌ Usage: study-mode-cli add <name> <type>[/]")
                console.print("[yellow]Example: study-mode-cli add firefox app[/]\n")
                sys.exit(1)

            name = args.args[0]
            item_type = args.args[1].lower()
            cmd_add(name, item_type)

        elif command == "remove" or command == "rm":
            if len(args.args) < 1:
                console.print("\n[red]❌ Usage: study-mode-cli remove <id|name>[/]\n")
                sys.exit(1)

            identifier = args.args[0]
            cmd_remove(identifier)

        # ====================================================================
        # BLOCK COMMANDS
        # ====================================================================

        elif command == "start":
            cmd_start()

        elif command == "stop":
            cmd_stop()

        elif command == "toggle":
            cmd_toggle()

        # ====================================================================
        # RESTORE COMMANDS
        # ====================================================================

        elif command == "list-restore":
            cmd_list_restore()

        elif command == "add-restore":
            if len(args.args) < 1:
                console.print("\n[red]❌ Usage: study-mode-cli add-restore <app>[/]")
                console.print(
                    "[yellow]Example: study-mode-cli add-restore firefox[/]\n"
                )
                sys.exit(1)

            app_name = args.args[0]
            cmd_add_restore(app_name)

        elif command == "remove-restore":
            if len(args.args) < 1:
                console.print(
                    "\n[red]❌ Usage: study-mode-cli remove-restore <app>[/]\n"
                )
                sys.exit(1)

            app_name = args.args[0]
            cmd_remove_restore(app_name)

        elif command == "restore":
            cmd_restore()

        elif command == "toggle-restore":
            cmd_toggle_restore()

        # ====================================================================
        # FOCUS LOCK COMMANDS
        # ====================================================================

        elif command == "set-timer":
            if len(args.args) < 1:
                console.print("\n[red]❌ Usage: study-mode-cli set-timer <minutes>[/]")
                console.print("[yellow]Example: study-mode-cli set-timer 25[/]\n")
                sys.exit(1)

            try:
                minutes = int(args.args[0])
                cmd_set_timer(minutes)
            except ValueError:
                console.print("\n[red]❌ Minutes must be a number[/]\n")
                sys.exit(1)

        elif command == "set-target-time":
            if len(args.args) < 2:
                console.print(
                    "\n[red]❌ Usage: study-mode-cli set-target-time <HH> <MM>[/]"
                )
                console.print(
                    "[yellow]Example: study-mode-cli set-target-time 14 30[/]\n"
                )
                sys.exit(1)

            try:
                hour = int(args.args[0])
                minute = int(args.args[1])
                cmd_set_target_time(hour, minute)
            except ValueError:
                console.print("\n[red]❌ Hours and minutes must be numbers[/]\n")
                sys.exit(1)

        elif command == "lock-status":
            cmd_lock_status()

        elif command == "clear-lock":
            cmd_clear_lock()

        # ====================================================================
        # UTILITY COMMANDS
        # ====================================================================

        elif command == "clear":
            cmd_clear()

        else:
            console.print(f"\n[red]❌ Unknown command: {command}[/]\n")
            print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Operation cancelled[/]\n")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/]\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
