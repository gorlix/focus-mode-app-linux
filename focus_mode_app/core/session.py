"""
core/session.py
Application tracking for restore on Wayland/X11.
Without xdotool - basic tracking only.
"""

import json
import time
from typing import List, Dict, Optional, Any
import psutil
import os

from focus_mode_app.config import SESSION_FILE, RESTORE_CONFIG_FILE


class SessionTracker:
    """Tracks applications killed during the active session.

    Manages the persistent list of applications eligible for restoration and
    tracks the active session's killed instances.
    """

    def __init__(self) -> None:
        """Initialize the SessionTracker and load the restore configuration."""
        self.killed_apps: List[Dict[str, Any]] = []
        self.restore_enabled: bool = False
        self.restore_list: Dict[str, Dict[str, Any]] = {}
        self.load_restore_config()

    def load_restore_config(self) -> None:
        """Load the list of applications configured for auto-restore from disk."""
        if not RESTORE_CONFIG_FILE.exists():
            self.restore_list = {}
            return

        try:
            with open(RESTORE_CONFIG_FILE, "r") as f:
                data = json.load(f)
            self.restore_list = data
            print(f"[INFO] Restore config loaded: {len(data)} apps")
        except Exception as e:
            print(f"[ERROR] Load restore config: {e}")
            self.restore_list = {}

    def save_restore_config(self) -> None:
        """Save the current restore configuration to disk."""
        try:
            RESTORE_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(RESTORE_CONFIG_FILE, "w") as f:
                json.dump(self.restore_list, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Save restore config: {e}")

    def add_to_restore(self, app_name: str) -> None:
        """Add an application to the auto-restore list.

        Args:
            app_name (str): The name of the application to be restored.
        """
        self.restore_list[app_name] = {"enabled": True, "added_at": time.time()}
        self.save_restore_config()
        print(f"[INFO] Added {app_name} to restore list")

    def remove_from_restore(self, app_name: str) -> None:
        """Remove an application from the auto-restore list.

        Args:
            app_name (str): The name of the application to remove.
        """
        if app_name in self.restore_list:
            del self.restore_list[app_name]
            self.save_restore_config()
            print(f"[INFO] Removed {app_name} from restore list")

    def capture_app_state(self, proc: psutil.Process) -> Optional[Dict[str, Any]]:
        """Capture the state of an application without xdotool (Wayland-compatible).

        Args:
            proc (psutil.Process): The psutil Process instance of the application.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the process state, or None if it fails.
        """
        try:
            app_state = {
                "pid": proc.pid,
                "name": proc.name(),
                "exe": proc.exe(),
                "cmdline": proc.cmdline(),
                "cwd": proc.cwd() if hasattr(proc, "cwd") else None,
                "timestamp": time.time(),
                "user": os.getenv("USER"),
            }
            return app_state

        except Exception as e:
            print(f"[ERROR] Capture state: {e}")
            return None

    def add_killed_app(self, app_name: str, app_state: Dict[str, Any]) -> None:
        """Add a killed application to the current session IF it is in the restore list.

        Args:
            app_name (str): The name of the application.
            app_state (Dict[str, Any]): The captured state dictionary.
        """
        if app_name not in self.restore_list:
            # Not in restore list, ignore
            return

        # Remove duplicates of the same app
        self.killed_apps = [a for a in self.killed_apps if a.get("name") != app_name]

        # Add
        self.killed_apps.append(app_state)
        self.save_session()
        print(f"[DEBUG] Tracked kill: {app_name}")

    def save_session(self) -> None:
        """Save the current session data (killed apps) to disk."""
        try:
            SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(SESSION_FILE, "w") as f:
                json.dump(self.killed_apps, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Save session: {e}")

    def load_session(self) -> List[Dict[str, Any]]:
        """Load the previous session data from disk.

        Returns:
            List[Dict[str, Any]]: The list of captured application states.
        """
        if not SESSION_FILE.exists():
            return []

        try:
            with open(SESSION_FILE, "r") as f:
                self.killed_apps = json.load(f)
            print(f"[INFO] Session loaded: {len(self.killed_apps)} apps")
            return self.killed_apps
        except Exception as e:
            print(f"[ERROR] Load session: {e}")
            return []

    def clear_session(self) -> None:
        """Clear the current session data from memory and delete the file."""
        self.killed_apps = []
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
        print("[INFO] Session cleared")

    def get_killed_apps(self) -> List[Dict[str, Any]]:
        """Return the list of applications killed during this session.

        Returns:
            List[Dict[str, Any]]: List of captured application states.
        """
        return self.killed_apps


# Global singleton
session_tracker = SessionTracker()
