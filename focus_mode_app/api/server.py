"""
FastAPI application definition and REST route handlers.

Binds the Pydantic models, authentication dependencies, and the business
logic to concrete HTTP endpoints.

Endpoint disponibili:
  GET  /api/state   — snapshot completo dello stato del daemon
  POST /api/toggle  — attiva/disattiva il process blocker
  POST /api/lock    — attiva focus lock (timer, target time, o HA lock indefinito)
  DELETE /api/lock  — rimuove il focus lock attivo
  POST /api/restore — abilita/disabilita il ripristino automatico app
"""

from typing import Any
from fastapi import FastAPI, Depends, HTTPException, status

from focus_mode_app.api.models import (
    StateResponse,
    ToggleRequest,
    ToggleResponse,
    BlockedItem,
    LockInfo,
    LockRequest,
    LockResponse,
    RestoreRequest,
    RestoreResponse,
)
from focus_mode_app.api.auth import verify_token
from focus_mode_app.api.signals import api_action_queue
from focus_mode_app.api.notifier import notify_state_change
from focus_mode_app.core.storage import blocked_items
from focus_mode_app.core.blocker import get_blocking_stats, is_restore_enabled


app = FastAPI(
    title="Focus Mode Backend API",
    description="REST API for remote control and Home Assistant integration of the Focus Mode daemon.",
    version="1.1.0",
)


# ---------------------------------------------------------------------------- #
# STATE
# ---------------------------------------------------------------------------- #


@app.get(
    "/api/state",
    response_model=StateResponse,
    summary="Retrieve Daemon State",
    description="Returns a comprehensive snapshot of the current daemon state.",
    dependencies=[Depends(verify_token)],
)
def get_state() -> Any:
    """
    Snapshot completo del daemon: blocker, elementi bloccati, focus lock, restore.
    """
    stats = get_blocking_stats()

    items = [
        BlockedItem(name=item["name"], type=item["type"]) for item in blocked_items
    ]

    focus_lock_dict = stats.get("focus_lock", {})
    focus_lock_info = LockInfo(
        locked=focus_lock_dict.get("locked", False),
        remaining_time=focus_lock_dict.get("remaining_time"),
        target_time=focus_lock_dict.get("target_time"),
    )

    return StateResponse(
        active=stats.get("blocking_active", False),
        blocked_items=items,
        focus_lock=focus_lock_info,
        restore_enabled=is_restore_enabled(),
    )


# ---------------------------------------------------------------------------- #
# TOGGLE
# ---------------------------------------------------------------------------- #


@app.post(
    "/api/toggle",
    response_model=ToggleResponse,
    summary="Toggle Blocker",
    description="Attiva o disattiva il process blocker tramite la coda thread-safe.",
    dependencies=[Depends(verify_token)],
)
def toggle_blocker(request: ToggleRequest) -> Any:
    """
    Accoda un'azione di toggle al thread principale GUI.
    Non muta lo stato direttamente per garantire sicurezza tra thread.
    """
    api_action_queue.put({"action": "toggle", "active": request.active})
    notify_state_change("focus_toggled", active=request.active)

    return ToggleResponse(
        active=request.active,
        status="success",
        message=f"Toggle action queued: active={request.active}.",
    )


# ---------------------------------------------------------------------------- #
# LOCK
# ---------------------------------------------------------------------------- #


@app.post(
    "/api/lock",
    response_model=LockResponse,
    summary="Activate Focus Lock",
    description=(
        "Attiva un focus lock che impedisce la disattivazione manuale del blocker. "
        "Modalità: 'timer' (N minuti), 'target' (fino a HH:MM), 'ha' (indefinito, solo HA può rimuoverlo)."
    ),
    dependencies=[Depends(verify_token)],
)
def activate_lock(request: LockRequest) -> Any:
    """
    Accoda l'attivazione del focus lock al thread GUI.
    Modalità 'ha' attiva un lock indefinito rimuovibile solo via DELETE /api/lock.
    """
    mode = request.mode

    if mode == "timer":
        if request.minutes is None or request.minutes <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Il campo 'minutes' deve essere un intero > 0 per mode='timer'.",
            )
        api_action_queue.put(
            {"action": "lock", "mode": "timer", "minutes": request.minutes}
        )
        notify_state_change("lock_activated", mode="timer", minutes=request.minutes)
        return LockResponse(
            locked=True,
            mode="timer",
            remaining_time=f"{request.minutes}m 0s",
            message=f"Timer lock accodato: {request.minutes} minuti.",
        )

    elif mode == "target":
        if request.hour is None or request.minute is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="I campi 'hour' e 'minute' sono richiesti per mode='target'.",
            )
        if not (0 <= request.hour <= 23 and 0 <= request.minute <= 59):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Ora non valida: hour deve essere 0-23, minute 0-59.",
            )
        api_action_queue.put(
            {
                "action": "lock",
                "mode": "target",
                "hour": request.hour,
                "minute": request.minute,
            }
        )
        notify_state_change(
            "lock_activated", mode="target", hour=request.hour, minute=request.minute
        )
        return LockResponse(
            locked=True,
            mode="target",
            remaining_time=None,
            message=f"Target time lock accodato: fino alle {request.hour:02d}:{request.minute:02d}.",
        )

    elif mode == "ha":
        api_action_queue.put({"action": "lock", "mode": "ha"})
        notify_state_change("lock_activated", mode="ha")
        return LockResponse(
            locked=True,
            mode="ha",
            remaining_time=None,
            message="HA Lock attivato. Solo DELETE /api/lock può rimuoverlo.",
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Modalità non valida: '{mode}'. Valori ammessi: 'timer', 'target', 'ha'.",
        )


@app.delete(
    "/api/lock",
    response_model=LockResponse,
    summary="Cancel Focus Lock",
    description="Rimuove qualsiasi focus lock attivo, incluso l'HA Lock indefinito.",
    dependencies=[Depends(verify_token)],
)
def cancel_lock() -> Any:
    """
    Accoda la rimozione del focus lock al thread GUI.
    È l'unico modo per rimuovere un HA Lock.
    """
    api_action_queue.put({"action": "unlock"})
    notify_state_change("lock_cancelled")

    return LockResponse(
        locked=False, mode="none", remaining_time=None, message="Focus lock rimosso."
    )


# ---------------------------------------------------------------------------- #
# AUTO-RESTORE
# ---------------------------------------------------------------------------- #


@app.post(
    "/api/restore",
    response_model=RestoreResponse,
    summary="Toggle Auto-Restore",
    description="Abilita o disabilita il ripristino automatico delle app alla disattivazione del blocker.",
    dependencies=[Depends(verify_token)],
)
def set_restore(request: RestoreRequest) -> Any:
    """
    Accoda la modifica dello stato auto-restore al thread GUI.
    """
    api_action_queue.put({"action": "set_restore", "enabled": request.enabled})
    notify_state_change("restore_changed", enabled=request.enabled)

    return RestoreResponse(
        enabled=request.enabled,
        message=f"Auto-restore {'abilitato' if request.enabled else 'disabilitato'}.",
    )
