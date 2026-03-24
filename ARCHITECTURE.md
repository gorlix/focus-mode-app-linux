# Focus Mode App Architecture

This document provides a high-level overview of how `focus-mode-app-linux` operates internally. It's intended for developers looking to understand the core mechanics, data flow, and trade-offs made for Linux/Wayland compatibility.

## High-Level Overview

The application is structured into two main components:

1. **The Core Blocker Daemon**: A background thread responsible for monitoring system processes and terminating those that appear in the blocklist.
2. **The User Interfaces (GUI & CLI)**: The frontend components allowing the user to view and modify the blocklist, handle focus locks, and toggle the blocking functionality.

### Entry Points

- `focus_mode_app/main.py`: The GUI entry point. It initializes all configurations, loads the blocklist, starts the daemon thread (`start_blocking_loop`), creates the system tray icon, and opens the PyQt6 `MainWindow`.
- `focus_mode_app/cli.py`: The CLI entry point. It allows interaction with the daemon state by modifying the shared JSON files.

## The Blocking Loop (`core/blocker.py`)

The blocking mechanism is heavily dependent on the `psutil` library. It avoids window manager-specific tools like `xdotool` or `wmctrl` to ensure strictly native support for both **X11** and **Wayland**.

**How it works:**

1. Every `BLOCKING_INTERVAL` seconds (default 2s), `start_blocking_loop` iterates over all system processes (`psutil.process_iter`).
2. **Native Apps**: It compares the `proc.info['name']` against the blocklist.
3. **Web Apps**: It checks the entire `proc.info['cmdline']` array to see if the target URL exists within the arguments (useful because browsers pass the URL as an argument to new spawned child processes or tabs).
4. If a match is found and the active PID is not `os.getpid()`, it forcefully terminates the process via `proc.kill()`.

### Thread Safety & State

The `blocking_active` boolean and the `_killed_pids` set reside entirely in `core/blocker.py`. When using the GUI, the toggle button modifies this global state directly. Note that the CLI operates heavily via the filesystem rather than IPC, meaning state toggling is partially done by reading/writing shared config status.

## Session Restoration (`core/session.py`)

To allow users to continue where they left off, the app attempts to capture process metadata before killing it.

1. Right before `proc.kill()` is called, the state is captured (PID, executable path, cmdline arguments, current working directory).
2. This state is serialized and dumped into `data/session_backup.json`.
3. When Focus Mode ends, `restore_all_apps()` parses this JSON and attempts to spin those processes back up using `subprocess.Popen` with the exact same binary and arguments.

### Wayland Limitations

Because Wayland severely limits a process's ability to arbitrarily introspect other windows (for security reasons), we *cannot* use CLI tools like `xdotool` to save window size or position, nor can we read the exact title. We only track raw processes. Consequently, restoring web apps heavily depends on the browser's ability to restore previous tabs when launched with the original CLI arguments.

## Data Persistence

State is persistently saved to local disk in JSON format inside the `data/` directory:

- `data/blocked_apps.json`: The core blocklist. Holds items formatted as `{"name": "...", "type": "app|webapp"}`.
- `data/restore_config.json`: A list of application names that have been marked as explicitly "auto-restore enabled".
- `data/session_backup.json`: A temporary state file. Overwritten whenever the blocking starts, holds the array of processes killed in the *current* session.

All access to these files routes through `core/storage.py` and `core/session.py`.
