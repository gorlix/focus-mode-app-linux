# Linux Focus Mode — HACS Integration Plugin Specification

## Overview

This document is the **complete specification** for the Home Assistant custom integration
(`custom_components/linux_focus_mode`) that acts as the Home Assistant counterpart to the
**Focus Mode App** running on a Linux desktop machine.

The Linux app is a productivity daemon that blocks distracting applications and websites
during study or work sessions. It exposes a REST API on port `8000` for remote control,
and sends push webhooks to Home Assistant every time its state changes.

This integration must make all features of the Linux app controllable and observable from
within Home Assistant — through entities, services, and automations — without requiring
any manual `configuration.yaml` editing from the user.

---

## Communication Architecture

```
Home Assistant (HACS Integration)
  │
  │  [Poll every 30s]  GET /api/state
  │  [Service calls]   POST/DELETE → /api/toggle, /api/lock, /api/restore
  │  Authorization: Bearer <token>
  │
  ▼
Focus Mode App  ←  Linux desktop, LAN IP, port 8000
  │
  │  [Push on state change]  POST → HA webhook (state_event_url)
  │  [Push on shutdown]      POST → HA webhook (dying_gasp_url)
  │
  ▼
Home Assistant webhook listener (in this integration)
  → triggers immediate coordinator refresh
```

**Key principle:** The integration operates bidirectionally.
- **HA → Linux app:** The coordinator calls REST endpoints to read and mutate state.
- **Linux app → HA:** The app pushes webhook events on every state change so entities
  update immediately, without waiting for the next polling cycle.

The polling (30s) acts only as a fallback sync mechanism. Real-time responsiveness comes
from the app's push webhooks.

---

## Linux App REST API Reference

### Authentication

All endpoints require an HTTP `Authorization` header with a Bearer token:

```
Authorization: Bearer <32-character hex token>
```

The token is generated once by the Linux app and stored in
`focus_mode_app/data/auth_token.txt`. The user copies it into the integration's
config flow during setup. Invalid tokens receive `401 Unauthorized`.

---

### GET /api/state

Returns the complete current state of the Focus Mode daemon.

**Response schema:**

```json
{
  "active": true,
  "restore_enabled": true,
  "blocked_items": [
    {"name": "firefox", "type": "app"},
    {"name": "web.whatsapp.com", "type": "webapp"}
  ],
  "focus_lock": {
    "locked": true,
    "remaining_time": "22m 14s",
    "target_time": null
  }
}
```

| Field | Type | Description |
|---|---|---|
| `active` | bool | Whether the process blocker is currently killing blocked apps |
| `restore_enabled` | bool | Whether auto-restore is active when blocking is disabled |
| `blocked_items` | array | List of all configured blocked items (apps and webapps) |
| `blocked_items[].name` | string | Process name (app) or URL substring (webapp) |
| `blocked_items[].type` | string | `"app"` or `"webapp"` |
| `focus_lock.locked` | bool | Whether any lock is currently active |
| `focus_lock.remaining_time` | string \| null | Human-readable remaining time (e.g. `"22m 14s"`). Null for HA Lock or no lock |
| `focus_lock.target_time` | string \| null | Target end time in `HH:MM` format. Null if not applicable |

**Note on focus_lock modes:** The `focus_lock` object in the state response does not
directly expose the lock mode. The HACS integration should infer HA Lock status from
whether `locked` is true AND `remaining_time` is null (HA Lock has no expiry).

---

### POST /api/toggle

Activates or deactivates the process blocker.

**Request body:**

```json
{"active": true}
```

**Response:**

```json
{
  "active": true,
  "status": "success",
  "message": "Toggle action queued: active=True."
}
```

The action is enqueued to the GUI thread for thread-safe execution.
The response confirms the action was queued, not necessarily already applied.

---

### POST /api/lock

Activates a focus lock. Three modes are available.

**Mode: timer** — lock for N minutes, then auto-expire

```json
{"mode": "timer", "minutes": 25}
```

**Mode: target** — lock until a specific clock time today (or tomorrow if past)

```json
{"mode": "target", "hour": 14, "minute": 30}
```

**Mode: ha** — indefinite lock, removable ONLY via `DELETE /api/lock`

```json
{"mode": "ha"}
```

**Response:**

```json
{
  "locked": true,
  "mode": "timer",
  "remaining_time": "25m 0s",
  "message": "Timer lock accodato: 25 minuti."
}
```

**Validation errors (422):**
- `mode="timer"` without `minutes > 0`
- `mode="target"` without valid `hour` (0–23) and `minute` (0–59)
- Unknown mode value

**Behavior:** Activating any lock also activates the blocker if it was not already active.

---

### DELETE /api/lock

Cancels any active focus lock, including the HA Lock.

No request body required.

**Response:**

```json
{
  "locked": false,
  "mode": "none",
  "remaining_time": null,
  "message": "Focus lock rimosso."
}
```

This is the **only way** to remove an HA Lock. The Linux app's GUI disables its own
"deactivate" and "change lock" buttons when an HA Lock is active.

---

### POST /api/restore

Enables or disables auto-restore (automatic relaunch of blocked apps when blocking ends).

**Request body:**

```json
{"enabled": false}
```

**Response:**

```json
{
  "enabled": false,
  "message": "Auto-restore disabilitato."
}
```

---

## Push Webhooks: Linux App → Home Assistant

The Linux app sends HTTP POST requests to two webhook URLs configured by the user in the
app's settings dialog (`data/ha_config.json`).

### State Event Webhook

Called on **every state change** (toggle, lock activation/cancellation, restore toggle).
The URL is configured by the user as `state_event_url` in the app's settings.

The HACS integration must register a webhook listener in Home Assistant to receive these
calls. When received, the coordinator should refresh immediately without waiting for the
next polling cycle.

**All possible event payloads:**

```json
{"event": "focus_toggled", "active": true}
{"event": "focus_toggled", "active": false}

{"event": "lock_activated", "mode": "timer", "minutes": 25}
{"event": "lock_activated", "mode": "target", "hour": 14, "minute": 30}
{"event": "lock_activated", "mode": "ha"}

{"event": "lock_cancelled"}

{"event": "restore_changed", "enabled": true}
{"event": "restore_changed", "enabled": false}
```

### Dying Gasp Webhook

Called **once on application shutdown**. The URL is configured separately as
`dying_gasp_url` in the app's settings.

```json
{"event": "dying_gasp", "status": "offline"}
```

When this event is received, the integration should mark the app as unavailable
(set all entities to `unavailable` state) until the next successful `GET /api/state`.

---

## Required Home Assistant Entities

The integration must expose the following entities. All derive their state from
`GET /api/state` polled by the coordinator.

### Switches

| Entity ID | Name | Maps to |
|---|---|---|
| `switch.linux_focus_mode_active` | Focus Mode | `state.active` |
| `switch.linux_focus_mode_ha_lock` | HA Lock | `state.focus_lock.locked && remaining_time == null` |
| `switch.linux_focus_mode_restore` | Auto-Restore | `state.restore_enabled` |

**Switch write behavior:**

| Switch | Turn ON | Turn OFF |
|---|---|---|
| Focus Mode Active | `POST /api/toggle {"active": true}` | `POST /api/toggle {"active": false}` |
| HA Lock | `POST /api/lock {"mode": "ha"}` | `DELETE /api/lock` |
| Auto-Restore | `POST /api/restore {"enabled": true}` | `POST /api/restore {"enabled": false}` |

**HA Lock switch special behavior:** When the HA Lock is active, the Focus Mode Active
switch should also be marked `unavailable` for writing (cannot turn OFF while locked).
Attempting to turn off Focus Mode via HA while HA Lock is active should be rejected.

### Sensors

| Entity ID | Name | Value | Unit |
|---|---|---|---|
| `sensor.linux_focus_mode_blocked_count` | Blocked Apps Count | `len(state.blocked_items)` | — |
| `sensor.linux_focus_mode_lock_remaining` | Lock Remaining Time | `state.focus_lock.remaining_time` or `"—"` | — |

### Binary Sensors

| Entity ID | Name | True when |
|---|---|---|
| `binary_sensor.linux_focus_mode_locked` | Focus Locked | `state.focus_lock.locked == true` |
| `binary_sensor.linux_focus_mode_available` | App Online | Last state fetch succeeded |

---

## Required Home Assistant Services

The integration must register the following services callable from automations, scripts,
and the HA UI. All services require the config entry entity as target.

| Service | Parameters | Action |
|---|---|---|
| `linux_focus_mode.focus_on` | — | `POST /api/toggle {"active": true}` |
| `linux_focus_mode.focus_off` | — | `POST /api/toggle {"active": false}` |
| `linux_focus_mode.lock_timer` | `minutes: int (required, >0)` | `POST /api/lock {"mode": "timer", "minutes": N}` |
| `linux_focus_mode.lock_target` | `hour: int (0-23)`, `minute: int (0-59)` | `POST /api/lock {"mode": "target", ...}` |
| `linux_focus_mode.lock_ha` | — | `POST /api/lock {"mode": "ha"}` |
| `linux_focus_mode.unlock` | — | `DELETE /api/lock` |
| `linux_focus_mode.restore_on` | — | `POST /api/restore {"enabled": true}` |
| `linux_focus_mode.restore_off` | — | `POST /api/restore {"enabled": false}` |

**Example automation using services:**

```yaml
automation:
  alias: "Start 25-minute Pomodoro from button press"
  trigger:
    - platform: state
      entity_id: input_button.start_pomodoro
  action:
    - service: linux_focus_mode.focus_on
    - service: linux_focus_mode.lock_timer
      data:
        minutes: 25
```

---

## Config Flow Requirements

The integration must be fully configurable through the Home Assistant UI — no
`configuration.yaml` editing required.

**Step 1 — Connection details:**
- `host`: IP address or hostname of the Linux machine (e.g. `192.168.1.100`)
- `port`: API port (default: `8000`)
- `token`: Bearer token copied from the Linux app's "Impostazioni HA" dialog

**Validation during setup:**
- Attempt `GET /api/state` with the provided credentials
- If response is 200 OK → setup succeeds, create config entry
- If response is 401 → show "Invalid token" error
- If connection fails → show "Cannot connect" error

**Step 2 — Webhook registration:**
After the config entry is created, the integration must display the webhook URL
that the user must paste into the Linux app's settings dialog as `state_event_url`.
The webhook URL is generated by HA and has the form:
`https://<ha-instance>/api/webhook/<webhook_id>`

---

## Availability & Error Handling

- If `GET /api/state` fails (network error, timeout), all entities should become
  `unavailable` until the next successful poll.
- If a dying gasp webhook is received, immediately mark all entities as `unavailable`.
- Service calls that fail (non-2xx response or connection error) should raise a
  `HomeAssistantError` with a user-facing message.
- The integration should handle the case where the Linux app is offline at HA startup
  gracefully (keep entities in `unavailable` state, retry on next poll cycle).

---

## HACS Manifest Requirements

The integration domain must be `linux_focus_mode`.

Required `manifest.json` fields:
- `domain`: `"linux_focus_mode"`
- `name`: `"Linux Focus Mode"`
- `version`: `"1.0.0"`
- `documentation`: link to the GitHub repo
- `issue_tracker`: link to GitHub issues
- `requirements`: must include `aiohttp` or `httpx` for async HTTP (prefer the HA
  built-in `aiohttp` session from `hass.helpers.aiohttp_client`)
- `config_flow`: `true`
- `iot_class`: `"local_polling"` (the integration polls a local LAN device)

---

## Design Decisions & Constraints (from the Linux app)

These decisions are fixed in the Linux app and must be respected by the integration:

1. **HA Lock is indefinite.** There is no timer. It persists until `DELETE /api/lock`
   is called. The app's GUI disables its own unlock controls while HA Lock is active —
   only the integration can remove it.

2. **Lock activation also starts blocking.** When any lock is activated via `POST /api/lock`,
   the Linux app automatically activates the blocker if it was inactive. The integration
   does not need to call `/api/toggle` separately before activating a lock.

3. **State mutation is async on the Linux side.** The API endpoints enqueue actions to the
   GUI thread and return immediately. The next `GET /api/state` call (polling or
   webhook-triggered refresh) will reflect the actual new state.

4. **Bearer token never changes.** The token is generated once at app first-run and
   stored on disk. The user does not need to re-enter it unless they delete
   `data/auth_token.txt` manually.

5. **Webhook URLs are free-form.** The Linux app accepts any HTTP/HTTPS URL for webhooks,
   including Cloudflare Tunnel domains and non-standard ports. The integration should
   present the HA-generated webhook URL in the config flow UI so the user can copy-paste
   it into the Linux app without manual construction.

6. **Blocked items list is read-only.** The `GET /api/state` response includes all blocked
   apps/webapps, but there is no API endpoint to add or remove items. The sensor showing
   the blocked count is purely informational.

7. **Auto-restore state is per-session.** The Linux app resets `restore_enabled` to `true`
   on each startup. The integration should not cache or assume its previous value.

---

## Testing Guidance

The integration should be testable against a live Linux app instance or a mock server
implementing the API contract above.

Minimum test cases:
- Config flow: successful setup with valid credentials
- Config flow: rejected setup with invalid token (401)
- Config flow: rejected setup with unreachable host
- State polling: entities reflect `GET /api/state` response
- Webhook receipt: coordinator refreshes immediately on push event
- Dying gasp: entities become `unavailable` on receipt
- Service: `focus_on` calls `POST /api/toggle {"active": true}`
- Service: `lock_timer` with valid and invalid `minutes` values
- Service: `lock_ha` then verify HA Lock switch is ON and Focus Mode switch rejects OFF
- Service: `unlock` removes HA Lock

---

## Source Repository Context

The Linux app source is at: `https://github.com/gorlix/focus-mode-app-linux`
Branch with the HA integration: `Home-Assistant-Integration`

API implementation files for reference:
- `focus_mode_app/api/server.py` — endpoint definitions
- `focus_mode_app/api/models.py` — Pydantic request/response schemas
- `focus_mode_app/api/notifier.py` — push webhook logic
- `focus_mode_app/core/focus_lock.py` — FocusLock class (LockMode enum, HA_LOCK semantics)
- `focus_mode_app/core/ha_config.py` — HA config persistence (webhook URLs, LLAT)

The interactive API documentation (Swagger UI) is available at `http://<host>:8000/docs`
when the Linux app is running. Use it to explore and test all endpoints.
