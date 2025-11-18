"""
core package
Contiene la logica di business dell'applicazione.
"""

from .storage import (
    blocked_items,
    save_blocked_items,
    load_blocked_items,
    add_blocked_item,
    remove_blocked_item,
    get_blocked_items,
)

from .blocker import (
    blocking_active,
    is_blocking_active,
    set_blocking_active,
    toggle_blocking,
    start_blocking_loop,
)

__all__ = [
    # Storage
    'blocked_items',
    'save_blocked_items',
    'load_blocked_items',
    'add_blocked_item',
    'remove_blocked_item',
    'get_blocked_items',
    # Blocker
    'blocking_active',
    'is_blocking_active',
    'set_blocking_active',
    'toggle_blocking',
    'start_blocking_loop',
]

