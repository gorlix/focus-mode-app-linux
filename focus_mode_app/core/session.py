"""
core/session.py
Tracciamento app per restore su Wayland/X11.
Senza xdotool - solo tracking basic.
"""

import json
import time
from typing import List, Dict, Optional
import psutil
import os

from focus_mode_app.config import SESSION_FILE, RESTORE_CONFIG_FILE


class SessionTracker:
    """Traccia app killate durante sessione."""

    def __init__(self):
        self.killed_apps: List[Dict] = []
        self.restore_enabled = False
        self.load_restore_config()

    def load_restore_config(self):
        """Carica lista app da ripristinare."""
        if not RESTORE_CONFIG_FILE.exists():
            self.restore_list = {}
            return

        try:
            with open(RESTORE_CONFIG_FILE) as f:
                data = json.load(f)
            self.restore_list = data
            print(f"[INFO] Restore config loaded: {len(data)} apps")
        except Exception as e:
            print(f"[ERROR] Load restore config: {e}")
            self.restore_list = {}

    def save_restore_config(self):
        """Salva configurazione restore."""
        try:
            RESTORE_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(RESTORE_CONFIG_FILE, 'w') as f:
                json.dump(self.restore_list, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Save restore config: {e}")

    def add_to_restore(self, app_name: str):
        """Aggiunge app alla lista restore."""
        self.restore_list[app_name] = {
            'enabled': True,
            'added_at': time.time()
        }
        self.save_restore_config()
        print(f"[INFO] Added {app_name} to restore list")

    def remove_from_restore(self, app_name: str):
        """Rimuove app dalla lista restore."""
        if app_name in self.restore_list:
            del self.restore_list[app_name]
            self.save_restore_config()
            print(f"[INFO] Removed {app_name} from restore list")

    def capture_app_state(self, proc: psutil.Process) -> Optional[Dict]:
        """
        Cattura stato app senza xdotool (Wayland compatible).
        """
        try:
            app_state = {
                'pid': proc.pid,
                'name': proc.name(),
                'exe': proc.exe(),
                'cmdline': proc.cmdline(),
                'cwd': proc.cwd() if hasattr(proc, 'cwd') else None,
                'timestamp': time.time(),
                'user': os.getenv('USER'),
            }
            return app_state

        except Exception as e:
            print(f"[ERROR] Capture state: {e}")
            return None

    def add_killed_app(self, app_name: str, app_state: Dict):
        """
        Aggiunge app killata SOLO se nella restore list.
        """
        if app_name not in self.restore_list:
            # Non è nella lista restore, ignora
            return

        # Rimuovi duplicati stesso app
        self.killed_apps = [
            a for a in self.killed_apps
            if a.get('name') != app_name
        ]

        # Aggiungi
        self.killed_apps.append(app_state)
        self.save_session()
        print(f"[DEBUG] Tracked kill: {app_name}")

    def save_session(self):
        """Salva sessione su disco."""
        try:
            SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(SESSION_FILE, 'w') as f:
                json.dump(self.killed_apps, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Save session: {e}")

    def load_session(self) -> List[Dict]:
        """Carica sessione precedente."""
        if not SESSION_FILE.exists():
            return []

        try:
            with open(SESSION_FILE) as f:
                self.killed_apps = json.load(f)
            print(f"[INFO] Session loaded: {len(self.killed_apps)} apps")
            return self.killed_apps
        except Exception as e:
            print(f"[ERROR] Load session: {e}")
            return []

    def clear_session(self):
        """Cancella sessione."""
        self.killed_apps = []
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
        print("[INFO] Session cleared")

    def get_killed_apps(self) -> List[Dict]:
        """Ritorna app killate."""
        return self.killed_apps


# Singleton globale
session_tracker = SessionTracker()
