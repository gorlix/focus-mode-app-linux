"""
cli package
Interfaccia command-line per Modalità Studio.
"""

from .commands import (
    cmd_status,
    cmd_list,
    cmd_add,
    cmd_remove,
    cmd_start,
    cmd_stop,
    cmd_toggle,
    cmd_clear,
)

__all__ = [
    "cmd_status",
    "cmd_list",
    "cmd_add",
    "cmd_remove",
    "cmd_start",
    "cmd_stop",
    "cmd_toggle",
    "cmd_clear",
]
