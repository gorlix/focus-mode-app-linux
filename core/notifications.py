"""
core/notifications.py
Sistema di notifiche desktop + GUI.
"""

import subprocess
from typing import Optional


def send_desktop_notification(title: str, message: str, icon: str = "dialog-information"):
    """
    Invia notifica desktop usando notify-send (Linux standard).
    """
    try:
        subprocess.run([
            'notify-send',
            '--urgency=normal',
            '--app-name=Focus Mode App',
            f'--icon={icon}',
            title,
            message
        ], timeout=5, check=False)
        print(f"[INFO] Notification sent: {title}")
    except Exception as e:
        print(f"[WARNING] Notification failed: {e}")


def notify_restore_complete(count: int, gui_instance=None):
    """
    Notifica completamento restore.
    Se GUI aperta → messaggio, altrimenti → notifica desktop.
    """
    message = f"✅ Restored {count} app{'s' if count != 1 else ''}"

    if gui_instance and hasattr(gui_instance, 'show_feedback'):
        # GUI è aperta
        gui_instance.show_feedback(message, duration=4000)
        print(f"[INFO] {message} (GUI)")
    else:
        # GUI chiusa → notifica desktop
        send_desktop_notification(
            "Restore Complete",
            message,
            "application-x-executable"
        )
        print(f"[INFO] {message} (notification)")


def notify_restore_disabled():
    """Notifica che restore è stato disabilitato."""
    send_desktop_notification(
        "Auto-Restore Disabled",
        "Apps will NOT be restored when disabling blocking",
        "dialog-warning"
    )


__all__ = [
    'send_desktop_notification',
    'notify_restore_complete',
    'notify_restore_disabled',
]
