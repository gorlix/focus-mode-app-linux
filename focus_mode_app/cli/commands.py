"""
cli/commands.py
CLI commands for the Focus Mode App.
Command-line interface to manage blocked apps, sessions, restore, and focus lock.
Supports both countdown timers and target times for the focus lock.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from focus_mode_app.core.storage import (
    add_blocked_item,
    remove_blocked_item,
    get_blocked_items,
)
from focus_mode_app.core.blocker import (
    is_blocking_active,
    set_blocking_active,
    toggle_blocking,
    set_restore_enabled,
    is_restore_enabled,
    get_blocking_stats,
)

console = Console()


# ============================================================================
# STATUS AND INFO COMMANDS
# ============================================================================


def cmd_status() -> None:
    """Show the current status of the block, session, and focus lock.

    Includes information on whether the block is active, blocked items count,
    apps to restore, and the focus lock timer.
    """
    stats = get_blocking_stats()

    status_emoji = "🔒" if stats["blocking_active"] else "🔓"
    status_text = "ACTIVE" if stats["blocking_active"] else "INACTIVE"
    status_color = "green" if stats["blocking_active"] else "red"

    restore_info = f"Apps to restore: [cyan]{stats['apps_to_restore_count']}[/]"
    restore_status = f"Auto-restore: [bold]{'ENABLED' if stats['auto_restore_enabled'] else 'DISABLED'}[/]"

    lock_info = stats.get("focus_lock", {})
    if lock_info.get("locked"):
        lock_status = (
            f"🔒 Focus Lock: [red]ACTIVE[/] - {lock_info['remaining_time']} remaining"
        )
    else:
        lock_status = "Focus Lock: [green]No active lock[/]"

    console.print()
    console.print(
        Panel(
            f"[bold {status_color}]{status_emoji} Block {status_text}[/]\n\n"
            f"Blocked items: [cyan]{stats['blocked_items_count']}[/]\n"
            f"Apps killed in session: [yellow]{stats['killed_apps_in_session']}[/]\n"
            f"{restore_info}\n"
            f"{restore_status}\n"
            f"{lock_status}\n"
            f"Check interval: [dim]{stats['blocking_interval']}s[/]",
            title="📊 Focus Mode App Status",
            border_style="blue",
            box=box.ROUNDED,
        )
    )


def cmd_list() -> None:
    """List all blocked elements (native apps and webapps).

    Displays the type and name of each element with a numeric index.
    """
    items = get_blocked_items()

    if not items:
        console.print("\n[yellow]ℹ️  No blocked elements[/]\n")
        return

    table = Table(title="🚫 Blocked Elements", box=box.ROUNDED)
    table.add_column("#", style="dim", width=4)
    table.add_column("Type", style="cyan", width=10)
    table.add_column("Name/URL", style="white")

    for idx, item in enumerate(items, 1):
        emoji = "📱" if item["type"] == "app" else "🌐"
        tipo = f"{emoji} App" if item["type"] == "app" else f"{emoji} Webapp"
        table.add_row(str(idx), tipo, item["name"])

    console.print()
    console.print(table)
    console.print()


def cmd_list_restore() -> None:
    """List all apps configured for automatic restoration.

    Shows which apps will be restored when the block is deactivated.
    """
    try:
        from focus_mode_app.core.session import session_tracker

        restore_list = session_tracker.restore_list

        if not restore_list:
            console.print("\n[yellow]ℹ️  No apps configured for restore[/]\n")
            return

        table = Table(title="♻️ Apps Configured for Auto-Restore", box=box.ROUNDED)
        table.add_column("#", style="dim", width=4)
        table.add_column("App", style="cyan")

        for idx, app_name in enumerate(restore_list.keys(), 1):
            table.add_row(str(idx), f"♻️ {app_name}")

        console.print()
        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/]\n")


# ============================================================================
# BLOCKED ITEMS MANAGEMENT COMMANDS
# ============================================================================


def cmd_add(name: str, item_type: str) -> None:
    """Add an element to the blocklist.

    Args:
        name (str): App name or webapp URL.
        item_type (str): Element type ('app' or 'webapp').
    """
    if item_type not in ["app", "webapp"]:
        console.print(f"\n[red]❌ Invalid type: {item_type}[/]")
        console.print("[yellow]Use 'app' or 'webapp'[/]\n")
        return

    if add_blocked_item(name, item_type):
        emoji = "📱" if item_type == "app" else "🌐"
        console.print(f"\n[green]✅ {emoji} '{name}' added to the list![/]\n")
    else:
        console.print(f"\n[yellow]⚠️  '{name}' is already in the list[/]\n")


def cmd_remove(identifier: str) -> None:
    """Remove an element from the blocklist.

    Accepts a 1-based numeric index or the exact name of the element.

    Args:
        identifier (str): The index (number) or exact name of the element.
    """
    items = get_blocked_items()

    if not items:
        console.print("\n[yellow]ℹ️  List is empty, nothing to remove[/]\n")
        return

    try:
        index = int(identifier) - 1
        if 0 <= index < len(items):
            item_name = items[index]["name"]
            if remove_blocked_item(index):
                console.print(f"\n[green]✅ '{item_name}' removed![/]\n")
                return
    except ValueError:
        pass

    for idx, item in enumerate(items):
        if item["name"] == identifier:
            if remove_blocked_item(idx):
                console.print(f"\n[green]✅ '{identifier}' removed![/]\n")
                return

    console.print(f"\n[red]❌ Element '{identifier}' not found[/]\n")


# ============================================================================
# BLOCK MANAGEMENT COMMANDS
# ============================================================================


def cmd_start() -> None:
    """Activate process blocking."""
    if is_blocking_active():
        console.print("\n[yellow]ℹ️  Block is already active[/]\n")
        return

    set_blocking_active(True)
    console.print("\n[green]🔒 Block ACTIVATED - Apps will be blocked[/]\n")


def cmd_stop() -> None:
    """Deactivate process blocking.

    Checks focus lock status before permitting deactivation.
    """
    if not is_blocking_active():
        console.print("\n[yellow]ℹ️  Block is already inactive[/]\n")
        return

    from focus_mode_app.core.blocker import can_disable_blocking

    can_disable, reason = can_disable_blocking()
    if not can_disable:
        console.print(f"\n[red]❌ {reason}[/]\n")
        return

    set_blocking_active(False)
    console.print("\n[red]🔓 Block DEACTIVATED[/]\n")

    try:
        from focus_mode_app.core.session import session_tracker

        killed_apps = session_tracker.get_killed_apps()

        if killed_apps:
            restored = len(killed_apps)
            console.print(
                f"[green]✅ Auto-restore completed: {restored} apps restored[/]\n"
            )
    except Exception as e:
        console.print(f"[yellow]⚠️  Error during auto-restore: {e}[/]\n")


def cmd_toggle() -> None:
    """Toggle the block state (active <-> inactive).

    Also handles automatic restoration upon deactivation.
    Checks focus lock status before disabling.
    """
    if is_blocking_active():
        from focus_mode_app.core.blocker import can_disable_blocking

        can_disable, reason = can_disable_blocking()
        if not can_disable:
            console.print(f"\n[red]❌ {reason}[/]\n")
            return

    new_state = toggle_blocking()

    if new_state:
        console.print("\n[green]🔒 Block ACTIVATED[/]\n")
    else:
        console.print("\n[red]🔓 Block DEACTIVATED[/]\n")


# ============================================================================
# RESTORE MANAGEMENT COMMANDS
# ============================================================================


def cmd_add_restore(app_name: str) -> None:
    """Add an app to the automatic restore list.

    The app will be restored when the block is deactivated.

    Args:
        app_name (str): Name of the app to add to the restore list.
    """
    try:
        from focus_mode_app.core.session import session_tracker

        session_tracker.add_to_restore(app_name)
        console.print(f"\n[green]✅ '{app_name}' added to auto-restore![/]\n")
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/]\n")


def cmd_remove_restore(app_name: str) -> None:
    """Remove an app from the automatic restore list.

    Args:
        app_name (str): Name of the app to remove from the restore list.
    """
    try:
        from focus_mode_app.core.session import session_tracker

        session_tracker.remove_from_restore(app_name)
        console.print(f"\n[green]✅ '{app_name}' removed from auto-restore![/]\n")
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/]\n")


def cmd_restore() -> None:
    """Manually restore all apps killed in the current session.

    Useful to force restore without waiting for block deactivation.
    """
    try:
        from focus_mode_app.core.restore import restore_all_apps
        from focus_mode_app.core.session import session_tracker

        apps = session_tracker.get_killed_apps()

        if not apps:
            console.print("\n[yellow]ℹ️  No apps to restore[/]\n")
            return

        console.print(f"\n[cyan]♻️  Restoring {len(apps)} apps...[/]")
        restored = restore_all_apps()
        console.print(f"[green]✅ Restored {restored} apps![/]\n")

    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/]\n")


def cmd_toggle_restore() -> None:
    """Enable or disable automatic restore for the current session.

    Allows controlling whether apps will be restored automatically.
    """
    current_state = is_restore_enabled()
    new_state = not current_state

    set_restore_enabled(new_state)

    status = "ENABLED" if new_state else "DISABLED"
    console.print(f"\n[cyan]Auto-restore {status}[/]\n")


# ============================================================================
# FOCUS LOCK MANAGEMENT COMMANDS
# ============================================================================


def cmd_set_timer(minutes: int) -> None:
    """Activate focus lock with a countdown timer.

    Args:
        minutes (int): Timer duration in minutes.
    """
    try:
        from focus_mode_app.core.focus_lock import focus_lock

        if focus_lock.set_timer_lock(minutes):
            console.print(f"\n[green]🔒 Focus Lock activated: {minutes} minutes[/]\n")

            if not is_blocking_active():
                cmd_start()
        else:
            console.print("\n[red]❌ Error activating timer[/]\n")

    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/]\n")


def cmd_set_target_time(hour: int, minute: int) -> None:
    """Activate focus lock until a target time.

    Supports setting the time for tomorrow if the hour has already passed today.

    Args:
        hour (int): Target hour (0-23).
        minute (int): Target minute (0-59).
    """
    try:
        from focus_mode_app.core.focus_lock import focus_lock

        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            console.print("\n[red]❌ Invalid time (HH: 0-23, MM: 0-59)[/]\n")
            return

        if focus_lock.set_target_time_lock(hour, minute):
            console.print(
                f"\n[green]🔒 Target Time Lock activated: until {hour:02d}:{minute:02d}[/]\n"
            )

            if not is_blocking_active():
                cmd_start()
        else:
            console.print("\n[red]❌ Error activating target time[/]\n")

    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/]\n")


def cmd_lock_status() -> None:
    """Show focus lock status with countdown and details."""
    try:
        from focus_mode_app.core.focus_lock import focus_lock

        info = focus_lock.get_lock_info()

        if info["locked"]:
            mode = "⏲️  TIMER" if info["mode"] == "timer" else "🕐 TARGET TIME"

            console.print()
            console.print(
                Panel(
                    f"[red]🔒 FOCUS LOCK ACTIVE[/]\n\n"
                    f"Mode: [cyan]{mode}[/]\n"
                    f"Remaining time: [yellow]{info['remaining_time']}[/]\n"
                    f"End time: [cyan]{info['end_time']}[/]\n"
                    f"Progress: [cyan]{info['progress_percentage']:.1f}%[/]",
                    title="Focus Lock Status",
                    border_style="red",
                    box=box.ROUNDED,
                )
            )
            console.print()
        else:
            console.print("\n[green]✅ No active lock[/]\n")

    except ImportError:
        console.print("\n[yellow]⚠️  Focus lock unavailable[/]\n")
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/]\n")


def cmd_clear_lock() -> None:
    """Manually remove focus lock (force unlock).

    Requires user confirmation.
    """
    try:
        from focus_mode_app.core.focus_lock import focus_lock
        from rich.prompt import Confirm

        if not focus_lock.is_locked():
            console.print("\n[yellow]ℹ️  No active lock[/]\n")
            return

        if Confirm.ask("\n[red]⚠️  Manually unlock the focus lock?[/]"):
            focus_lock.force_unlock()
            console.print("\n[green]✅ Focus lock removed![/]\n")
        else:
            console.print("\n[yellow]Operation cancelled[/]\n")

    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/]\n")


# ============================================================================
# LIST MANAGEMENT COMMANDS
# ============================================================================


def cmd_clear() -> None:
    """Remove all elements from the blocklist.

    Requires user confirmation before proceeding.
    """
    if not get_blocked_items():
        console.print("\n[yellow]ℹ️  List is already empty[/]\n")
        return

    from rich.prompt import Confirm

    if Confirm.ask("\n[red]⚠️  Remove ALL elements?[/]"):
        from focus_mode_app.core.storage import clear_blocked_items

        clear_blocked_items()
        console.print("\n[green]✅ List cleared![/]\n")
    else:
        console.print("\n[yellow]Operation cancelled[/]\n")


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "cmd_status",
    "cmd_list",
    "cmd_list_restore",
    "cmd_add",
    "cmd_remove",
    "cmd_start",
    "cmd_stop",
    "cmd_toggle",
    "cmd_add_restore",
    "cmd_remove_restore",
    "cmd_restore",
    "cmd_toggle_restore",
    "cmd_set_timer",
    "cmd_set_target_time",
    "cmd_lock_status",
    "cmd_clear_lock",
    "cmd_clear",
]
