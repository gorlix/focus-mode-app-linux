"""
core/ha_client.py
Home Assistant Native App Integration client.

Responsibilities:
1. Device registration (one-time) via POST /api/mobile_app/registrations
2. Sensor registration via webhook
3. Full-state push in native update_sensor_states format
4. Command reception via persistent WebSocket to HA event bus

Threading model: all HTTP calls use requests (fire-and-forget threads).
WebSocket runs in its own daemon thread with exponential reconnect.
"""

import json
import logging
import platform
import socket
import threading
import time
import uuid
from typing import Any

import requests

from focus_mode_app.config import DATA_DIR
from focus_mode_app.api.signals import api_action_queue

_LOGGER = logging.getLogger(__name__)

_APP_ID = "linux_focus_mode"
_APP_VERSION = "1.0.0"

_SENSOR_DEFS = [
    {"unique_id": "focus_active",    "name": "Focus Active",       "type": "binary_sensor"},
    {"unique_id": "ha_lock_active",  "name": "HA Lock Active",     "type": "binary_sensor"},
    {"unique_id": "restore_enabled", "name": "Auto-Restore",       "type": "binary_sensor"},
    {"unique_id": "focus_locked",    "name": "Focus Locked",       "type": "binary_sensor"},
    {"unique_id": "blocked_count",   "name": "Blocked Apps Count", "type": "sensor"},
    {"unique_id": "lock_remaining",  "name": "Lock Remaining",     "type": "sensor"},
    {"unique_id": "app_online",      "name": "App Online",         "type": "binary_sensor"},
]

# Maps HA command actions → api_action_queue entries
_ACTION_MAP: dict[str, Any] = {
    "focus_on":    lambda d: {"action": "toggle", "active": True},
    "focus_off":   lambda d: {"action": "toggle", "active": False},
    "lock_timer":  lambda d: {"action": "lock", "mode": "timer",  "minutes": d.get("minutes", 25)},
    "lock_target": lambda d: {"action": "lock", "mode": "target", "hour": d.get("hour", 0), "minute": d.get("minute", 0)},
    "lock_ha":     lambda d: {"action": "lock", "mode": "ha"},
    "unlock":      lambda d: {"action": "unlock"},
    "restore_on":  lambda d: {"action": "set_restore", "enabled": True},
    "restore_off": lambda d: {"action": "set_restore", "enabled": False},
}


class HAClient:
    """Manages HA native app registration, state push, and command reception."""

    def __init__(self, ha_url: str, llat: str, webhook_id: str = "") -> None:
        self.ha_url = ha_url.rstrip("/")
        self.llat = llat
        self.webhook_id = webhook_id
        self._ws_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_device(self) -> str:
        """Register this machine as a mobile_app device. Returns webhook_id."""
        url = f"{self.ha_url}/api/mobile_app/registrations"
        payload = {
            "device_id": _stable_device_id(),
            "app_id": _APP_ID,
            "app_name": "Linux Focus Mode",
            "app_version": _APP_VERSION,
            "device_name": socket.gethostname(),
            "manufacturer": "Linux",
            "model": platform.machine(),
            "os_name": "Linux",
            "os_version": platform.release(),
            "supports_encryption": False,
        }
        resp = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {self.llat}"},
            timeout=10,
        )
        resp.raise_for_status()
        self.webhook_id = resp.json()["webhook_id"]
        _LOGGER.info("Device registered, webhook_id=%s", self.webhook_id)
        return self.webhook_id

    def register_sensors(self) -> None:
        """Register all sensors via webhook (idempotent — safe to call every startup)."""
        if not self.webhook_id:
            raise RuntimeError("No webhook_id — call register_device() first")
        url = f"{self.ha_url}/api/webhook/{self.webhook_id}"
        for sensor in _SENSOR_DEFS:
            try:
                r = requests.post(
                    url,
                    json={"type": "register_sensor", "data": sensor},
                    timeout=10,
                )
                r.raise_for_status()
            except requests.RequestException as exc:
                _LOGGER.warning("Sensor registration failed (%s): %s", sensor["unique_id"], exc)

    # ------------------------------------------------------------------
    # State push
    # ------------------------------------------------------------------

    def push_state(self, state: dict[str, Any]) -> None:
        """Push full state snapshot to HA in native update_sensor_states format."""
        if not self.webhook_id:
            return

        lock = state.get("focus_lock", {})
        locked = bool(lock.get("locked", False))
        remaining = lock.get("remaining_time")

        sensors = [
            {"unique_id": "focus_active",    "state": bool(state.get("active", False)),         "type": "binary_sensor"},
            {"unique_id": "restore_enabled",  "state": bool(state.get("restore_enabled", True)), "type": "binary_sensor"},
            {"unique_id": "focus_locked",     "state": locked,                                    "type": "binary_sensor"},
            {"unique_id": "ha_lock_active",   "state": locked and remaining is None,              "type": "binary_sensor"},
            {"unique_id": "blocked_count",    "state": len(state.get("blocked_items", [])),       "type": "sensor"},
            {"unique_id": "lock_remaining",   "state": remaining or "—",                          "type": "sensor"},
            {"unique_id": "app_online",       "state": True,                                       "type": "binary_sensor"},
        ]
        payload = {"type": "update_sensor_states", "data": sensors}
        url = f"{self.ha_url}/api/webhook/{self.webhook_id}"

        threading.Thread(
            target=self._post_silent,
            args=(url, payload),
            daemon=True,
        ).start()

    def send_dying_gasp(self) -> None:
        """Synchronous dying gasp — called at shutdown before process exits."""
        if not self.webhook_id:
            return
        url = f"{self.ha_url}/api/webhook/{self.webhook_id}"
        try:
            requests.post(
                url,
                json={"event": "dying_gasp", "status": "offline"},
                timeout=3,
            )
        except requests.RequestException as exc:
            _LOGGER.warning("Dying gasp failed: %s", exc)

    def _post_silent(self, url: str, payload: dict) -> None:
        try:
            requests.post(url, json=payload, timeout=5)
        except requests.RequestException as exc:
            _LOGGER.warning("State push failed: %s", exc)

    # ------------------------------------------------------------------
    # WebSocket command listener
    # ------------------------------------------------------------------

    def start_command_listener(self) -> None:
        """Start the persistent WebSocket thread that receives HA commands."""
        if self._ws_thread and self._ws_thread.is_alive():
            return
        self._stop_event.clear()
        self._ws_thread = threading.Thread(
            target=self._ws_loop,
            name="HACommandListener",
            daemon=True,
        )
        self._ws_thread.start()
        _LOGGER.info("HA command listener started")

    def stop_command_listener(self) -> None:
        """Signal the WebSocket thread to stop."""
        self._stop_event.set()

    def _ws_loop(self) -> None:
        """Reconnect loop with exponential backoff."""
        delay = 2
        while not self._stop_event.is_set():
            try:
                self._ws_session()
                delay = 2
            except Exception as exc:
                _LOGGER.warning("WS disconnected: %s — retry in %ds", exc, delay)
            if not self._stop_event.is_set():
                time.sleep(delay)
                delay = min(delay * 2, 60)

    def _ws_session(self) -> None:
        """Single WebSocket session: authenticate → subscribe → receive."""
        try:
            import websocket
        except ImportError:
            _LOGGER.error("websocket-client not installed — HA command reception unavailable")
            self._stop_event.set()
            return

        ws_url = (
            self.ha_url
            .replace("https://", "wss://")
            .replace("http://", "ws://")
        ) + "/api/websocket"

        ws = websocket.WebSocket()
        ws.connect(ws_url, timeout=10)

        msg = json.loads(ws.recv())
        if msg.get("type") != "auth_required":
            ws.close()
            raise RuntimeError(f"Expected auth_required, got {msg.get('type')}")

        ws.send(json.dumps({"type": "auth", "access_token": self.llat}))
        msg = json.loads(ws.recv())
        if msg.get("type") != "auth_ok":
            ws.close()
            raise RuntimeError("HA authentication failed — check LLAT")

        ws.send(json.dumps({
            "type": "subscribe_events",
            "id": 1,
            "event_type": "linux_focus_mode_command",
        }))
        msg = json.loads(ws.recv())
        if not msg.get("success"):
            ws.close()
            raise RuntimeError(f"Event subscription failed: {msg}")

        _LOGGER.info("Subscribed to linux_focus_mode_command events")

        while not self._stop_event.is_set():
            ws.settimeout(5)
            try:
                raw = ws.recv()
            except websocket.WebSocketTimeoutException:
                continue
            if not raw:
                break
            message = json.loads(raw)
            if message.get("type") == "event":
                data = message.get("event", {}).get("data", {})
                self._dispatch(data)

        ws.close()

    def _dispatch(self, data: dict) -> None:
        action = data.get("action", "")
        factory = _ACTION_MAP.get(action)
        if factory is None:
            _LOGGER.warning("Unknown HA command action: %s", action)
            return
        entry = factory(data)
        api_action_queue.put(entry)
        _LOGGER.debug("HA command dispatched: %s → %s", action, entry)


# ------------------------------------------------------------------
# Module-level singleton + helpers
# ------------------------------------------------------------------

_client: HAClient | None = None


def get_client() -> HAClient | None:
    return _client


def init_client(ha_url: str, llat: str, webhook_id: str = "") -> HAClient:
    global _client
    _client = HAClient(ha_url=ha_url, llat=llat, webhook_id=webhook_id)
    return _client


def push_current_state() -> bool:
    """
    Push current daemon state to HA using the native client.
    Returns True if sent, False if client not configured.
    """
    if _client is None or not _client.webhook_id:
        return False

    from focus_mode_app.core.blocker import get_blocking_stats, is_restore_enabled
    from focus_mode_app.core.storage import blocked_items

    stats = get_blocking_stats()
    state = {
        "active": stats.get("blocking_active", False),
        "restore_enabled": is_restore_enabled(),
        "blocked_items": blocked_items,
        "focus_lock": stats.get("focus_lock", {}),
    }
    _client.push_state(state)
    return True


def _stable_device_id() -> str:
    """Stable UUID for this machine, persisted in data/device_id.txt."""
    id_file = DATA_DIR / "device_id.txt"
    if id_file.exists():
        stored = id_file.read_text().strip()
        if stored:
            return stored
    device_id = str(uuid.uuid4())
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    id_file.write_text(device_id)
    return device_id
