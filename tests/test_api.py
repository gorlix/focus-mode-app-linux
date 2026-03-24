"""
tests/test_api.py
Headless integration tests for the Focus Mode FastAPI backend.
Validates authentication boundaries and thread-safe Tkinter queue polling.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import queue

from focus_mode_app.api.server import app
from focus_mode_app.api.auth import verify_token
from focus_mode_app.api.signals import api_action_queue

client = TestClient(app)

def override_verify_token():
    """Mock dependency to bypass filesystem token validation during tests."""
    return "test_token_123"

@pytest.fixture(autouse=True)
def setup_auth_override():
    """Injects the token override before each test, except where removed."""
    app.dependency_overrides[verify_token] = override_verify_token
    yield
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def clear_queue():
    """Ensures the thread-safe queue is empty before and after each test."""
    while not api_action_queue.empty():
        try:
            api_action_queue.get_nowait()
            api_action_queue.task_done()
        except queue.Empty:
            break
    yield
    while not api_action_queue.empty():
        try:
            api_action_queue.get_nowait()
            api_action_queue.task_done()
        except queue.Empty:
            break

def test_get_state_unauthorized():
    """Ensure accessing endpoints without a valid Bearer token returns 401."""
    # Remove override to test real auth dependency
    app.dependency_overrides.clear()

    response = client.get("/api/state")
    assert response.status_code == 403 or response.status_code == 401


@patch("focus_mode_app.api.server.get_blocking_stats")
def test_get_state_authorized(mock_stats):
    """
    Ensure the /api/state endpoint returns exactly the expected Pydantic schema
    by mocking the internal core logic of the daemon.
    """
    mock_stats.return_value = {
        "blocking_active": True,
        "focus_lock": {"locked": False, "remaining_time": None, "target_time": None}
    }

    # Temporarily override the bound list of blocked_items
    import focus_mode_app.api.server
    original_items = focus_mode_app.api.server.blocked_items.copy()
    focus_mode_app.api.server.blocked_items.clear()
    focus_mode_app.api.server.blocked_items.extend([
        {"name": "discord", "type": "app"}
    ])

    try:
        response = client.get("/api/state")

        assert response.status_code == 200
        data = response.json()
        assert data["active"] is True
        assert len(data["blocked_items"]) == 1
        assert data["blocked_items"][0] == {"name": "discord", "type": "app"}
        assert data["focus_lock"]["locked"] is False
    finally:
        focus_mode_app.api.server.blocked_items.clear()
        focus_mode_app.api.server.blocked_items.extend(original_items)


def test_toggle_blocker_queues_message():
    """
    Ensure that POST /api/toggle safely enqueues the action rather than
    directly mutating the running GUI, preventing PyQt/Tkinter crashes.
    """
    response = client.post(
        "/api/toggle",
        json={"active": True}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["active"] is True
    assert data["status"] == "success"

    # Crucially verify the Thread-safe Queue acts as a buffer
    assert api_action_queue.qsize() == 1

    msg = api_action_queue.get_nowait()
    assert msg == {"action": "toggle", "active": True}
    api_action_queue.task_done()

    assert api_action_queue.empty() is True
