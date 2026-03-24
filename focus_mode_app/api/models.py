"""
Pydantic schemas governing request and response validation for the API.

These models generate the OpenAPI documentation automatically via FastAPI.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class BlockedItem(BaseModel):
    """
    Representation of a single blocked target.
    """
    name: str = Field(..., description="The name of the blocked app/website.", example="discord")
    type: str = Field(..., description="The category type: 'app' or 'webapp'.", example="app")


class LockInfo(BaseModel):
    """
    Metadata concerning the current Focus Lock status.
    """
    locked: bool = Field(..., description="True if a focus lock prevents manual disabling.")
    remaining_time: Optional[str] = Field(None, description="Time until the lock naturally expires.", example="15m 30s")
    target_time: Optional[str] = Field(None, description="The absolute finish time of the lock.", example="15:30")


class StateResponse(BaseModel):
    """
    Complete snapshot of the Focus Mode daemon's state.
    """
    active: bool = Field(..., description="Whether the blocker is currently killing processes.")
    blocked_items: List[BlockedItem] = Field(..., description="Array of all configured blocked items.")
    focus_lock: LockInfo = Field(..., description="Lock constraints currently in effect.")


class ToggleRequest(BaseModel):
    """
    Payload for activating or deactivating the blocker.
    """
    active: bool = Field(..., description="Set to true to activate blocking, false to deactivate.")


class ToggleResponse(BaseModel):
    """
    Result of a toggle request.
    """
    active: bool = Field(..., description="The resulting status of the blocker after the request.")
    status: str = Field(..., description="'success' or 'error' depending on the operation's outcome.")
    message: str = Field(..., description="Human readable context message regarding the operation.")
