"""
core/focus_lock.py
Timed lock system to prevent premature disabling of focus mode.
Supports timer countdown and target time locking.
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from enum import Enum


class LockMode(Enum):
    """Available locking modes."""

    NONE = "none"
    TIMER = "timer"
    TARGET_TIME = "target_time"


class FocusLock:
    """Manages the timed locking of the deactivation feature.

    Prevents the user from disabling the focus block before the
    timer expires or the expected target time is reached.
    """

    def __init__(self) -> None:
        """Initialize the FocusLock state."""
        self.lock_enabled: bool = False
        self.lock_mode: LockMode = LockMode.NONE
        self.lock_end_time: Optional[float] = None
        self.lock_duration: Optional[int] = None
        self.lock_start_time: Optional[float] = None

    def set_timer_lock(self, duration_minutes: int) -> bool:
        """Activate the lock with a countdown timer.

        Args:
            duration_minutes (int): The duration of the lock in minutes.

        Returns:
            bool: True if the lock was successfully activated, False if invalid duration.
        """
        if duration_minutes <= 0:
            return False

        self.lock_enabled = True
        self.lock_mode = LockMode.TIMER
        self.lock_duration = duration_minutes
        self.lock_start_time = time.time()
        self.lock_end_time = time.time() + (duration_minutes * 60)

        print(f"[INFO] Timer lock activated: {duration_minutes} minutes")
        return True

    def set_target_time_lock(self, target_hour: int, target_minute: int) -> bool:
        """Activate the lock until a specific target time.

        If the specified time has already passed today, it sets the target
        to the same time tomorrow.

        Args:
            target_hour (int): The target hour (0-23).
            target_minute (int): The target minute (0-59).

        Returns:
            bool: True if the lock was successfully activated.
        """
        now = datetime.now()
        target = now.replace(
            hour=target_hour, minute=target_minute, second=0, microsecond=0
        )

        if target <= now:
            target += timedelta(days=1)

        self.lock_enabled = True
        self.lock_mode = LockMode.TARGET_TIME
        self.lock_start_time = time.time()
        self.lock_end_time = target.timestamp()
        self.lock_duration = int((self.lock_end_time - self.lock_start_time) / 60)

        print(
            f"[INFO] Target time lock activated: until {target_hour:02d}:{target_minute:02d}"
        )
        return True

    def is_locked(self) -> bool:
        """Check whether the focus block is currently actively locked.

        Automatically clears the lock if the duration has expired.

        Returns:
            bool: True if still locked, False if expired or not enabled.
        """
        if not self.lock_enabled:
            return False

        if self.lock_end_time is None:
            return False

        if time.time() >= self.lock_end_time:
            self.clear_lock()
            return False

        return True

    def get_remaining_time(self) -> Tuple[int, int]:
        """Calculate the remaining time until the lock expires.

        Returns:
            Tuple[int, int]: A tuple containing the (minutes, seconds) remaining.
        """
        if not self.is_locked() or self.lock_end_time is None:
            return (0, 0)

        remaining_seconds = int(self.lock_end_time - time.time())
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60

        return (minutes, seconds)

    def get_progress_percentage(self) -> float:
        """Calculate the completion percentage of the current lock.

        Returns:
            float: A percentage value between 0.0 and 100.0.
        """
        if not self.is_locked() or not self.lock_start_time or not self.lock_end_time:
            return 100.0

        total_duration = self.lock_end_time - self.lock_start_time
        elapsed = time.time() - self.lock_start_time

        return min(100.0, (elapsed / total_duration) * 100)

    def clear_lock(self) -> None:
        """Manually remove the active focus lock."""
        self.lock_enabled = False
        self.lock_mode = LockMode.NONE
        self.lock_end_time = None
        self.lock_duration = None
        self.lock_start_time = None

        print("[INFO] Focus lock cleared")

    def force_unlock(self, password: Optional[str] = None) -> bool:
        """Forcibly unlock the focus mode, optionally requiring a password.

        Args:
            password (Optional[str], optional): Developer password to bypass the lock.
                                                Defaults to None.

        Returns:
            bool: True if successfully unlocked, False otherwise.
        """
        if password is None:
            print("[WARNING] Force unlock requested")
            self.clear_lock()
            return True

        return False

    def get_lock_info(self) -> Dict[str, Any]:
        """Retrieve complete information about the current lock state.

        Returns:
            Dict[str, Any]: A dictionary detailing lock mode, status, and remaining time.
        """
        if not self.is_locked() or self.lock_end_time is None:
            return {"locked": False, "mode": "none", "remaining_time": "00:00"}

        minutes, seconds = self.get_remaining_time()

        return {
            "locked": True,
            "mode": self.lock_mode.value,
            "duration_minutes": self.lock_duration,
            "remaining_time": f"{minutes:02d}:{seconds:02d}",
            "remaining_minutes": minutes,
            "remaining_seconds": seconds,
            "progress_percentage": self.get_progress_percentage(),
            "end_time": datetime.fromtimestamp(self.lock_end_time).strftime("%H:%M:%S"),
        }


focus_lock = FocusLock()
