"""
core/notifications.py
System for desktop and GUI notifications.
"""

import subprocess
from typing import Optional, Any


def send_desktop_notification(
    title: str, message: str, icon: str = "dialog-information"
) -> None:
    """Send a desktop notification using notify-send (standard Linux tool).

    Args:
        title (str): The title of the notification.
        message (str): The body text of the notification.
        icon (str, optional): The name of the system icon to display. Defaults to "dialog-information".
    """
    try:
        subprocess.run(
            [
                "notify-send",
                "--urgency=normal",
                "--app-name=Focus Mode App",
                f"--icon={icon}",
                title,
                message,
            ],
            timeout=5,
            check=False,
        )
        print(f"[INFO] Notification sent: {title}")
    except Exception as e:
        print(f"[WARNING] Notification failed: {e}")


def notify_restore_complete(count: int, gui_instance: Optional[Any] = None) -> None:
    """Notify the user that the session restore is complete.

    If the GUI is open, it shows an in-app feedback message.
    Otherwise, it triggers a desktop notification.

    Args:
        count (int): The number of applications that were restored.
        gui_instance (Optional[Any], optional): The active GUI instance if present. Defaults to None.
    """
    message = f"✅ Restored {count} app{'s' if count != 1 else ''}"

    if gui_instance and hasattr(gui_instance, "show_feedback"):
        # GUI is open
        gui_instance.show_feedback(message, duration=4000)
        print(f"[INFO] {message} (GUI)")
    else:
        # GUI is closed -> triggers desktop notification
        send_desktop_notification(
            "Restore Complete", message, "application-x-executable"
        )
        print(f"[INFO] {message} (notification)")


def notify_restore_disabled() -> None:
    """Notify the user that auto-restore has been disabled for this session."""
    send_desktop_notification(
        "Auto-Restore Disabled",
        "Apps will NOT be restored when disabling blocking",
        "dialog-warning",
    )


__all__ = [
    "send_desktop_notification",
    "notify_restore_complete",
    "notify_restore_disabled",
]
