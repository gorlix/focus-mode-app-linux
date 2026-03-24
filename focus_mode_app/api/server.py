"""
FastAPI application definition and REST route handlers.

Binds the Pydantic models, authentication dependencies, and the business
logic to concrete HTTP endpoints.
"""

from typing import Any
from fastapi import FastAPI, Depends

from focus_mode_app.api.models import (
    StateResponse,
    ToggleRequest,
    ToggleResponse,
    BlockedItem,
    LockInfo
)
from focus_mode_app.api.auth import verify_token
from focus_mode_app.api.signals import api_action_queue
from focus_mode_app.core.storage import blocked_items
from focus_mode_app.core.blocker import get_blocking_stats


app = FastAPI(
    title="Focus Mode Backend API",
    description="REST API for remote control and integration of the Focus Mode daemon.",
    version="1.0.0"
)


@app.get(
    "/api/state",
    response_model=StateResponse,
    summary="Retrieve Blocker State",
    description="Returns a comprehensive snapshot of the current daemon state, including active block rules and locks.",
    response_description="The structured daemon state.",
    dependencies=[Depends(verify_token)]
)
def get_state() -> Any:
    """
    HTTP GET endpoint to fetch the current operational state of the blocking engine.

    Reads from the global `blocked_items` cache and fetches active blocking statistics
    to construct the exact schema required by Home Assistant.
    """
    stats = get_blocking_stats()

    # Safely duplicate the blocked items list
    items = [
        BlockedItem(name=item["name"], type=item["type"])
        for item in blocked_items
    ]

    focus_lock_dict = stats.get("focus_lock", {})
    focus_lock_info = LockInfo(
        locked=focus_lock_dict.get("locked", False),
        remaining_time=focus_lock_dict.get("remaining_time"),
        target_time=focus_lock_dict.get("target_time")
    )

    return StateResponse(
        active=stats.get("blocking_active", False),
        blocked_items=items,
        focus_lock=focus_lock_info
    )


@app.post(
    "/api/toggle",
    response_model=ToggleResponse,
    summary="Toggle Blocker",
    description="Requests a state change for the process blocker via a thread-safe Queue.",
    response_description="Confirmation of the requested toggle operation.",
    dependencies=[Depends(verify_token)]
)
def toggle_blocker(request: ToggleRequest) -> Any:
    """
    HTTP POST endpoint to toggle the blocking engine on or off.

    Crucially, this does NOT mutate the process blocker directly. Instead, it places
    the toggle action into a thread-safe Queue that the main Tkinter GUI polls,
    ensuring that visual updates happen safely on the main thread.
    """
    api_action_queue.put({"action": "toggle", "active": request.active})

    return ToggleResponse(
        active=request.active,
        status="success",
        message=f"Toggle action queued: active={request.active}."
    )
