"""
core/focus_lock.py
Sistema di blocco temporizzato per impedire disattivazione prematura.
Supporta timer countdown e target time.
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Tuple
from enum import Enum


class LockMode(Enum):
    """Modalità di blocco disponibili."""
    NONE = "none"
    TIMER = "timer"
    TARGET_TIME = "target_time"


class FocusLock:
    """
    Gestisce il blocco temporizzato della disattivazione.
    Impedisce di disattivare il blocco prima della scadenza.
    """

    def __init__(self):
        self.lock_enabled = False
        self.lock_mode = LockMode.NONE
        self.lock_end_time: Optional[float] = None
        self.lock_duration: Optional[int] = None
        self.lock_start_time: Optional[float] = None

    def set_timer_lock(self, duration_minutes: int) -> bool:
        """
        Attiva lock con timer countdown.

        Args:
            duration_minutes: Durata in minuti

        Returns:
            True se lock attivato con successo
        """
        if duration_minutes <= 0:
            return False

        self.lock_enabled = True
        self.lock_mode = LockMode.TIMER
        self.lock_duration = duration_minutes
        self.lock_start_time = time.time()
        self.lock_end_time = time.time() + (duration_minutes * 60)

        print(f"[INFO] Timer lock attivato: {duration_minutes} minuti")
        return True

    def set_target_time_lock(self, target_hour: int, target_minute: int) -> bool:
        """
        Attiva lock fino a orario target.

        Args:
            target_hour: Ora target (0-23)
            target_minute: Minuto target (0-59)

        Returns:
            True se lock attivato con successo
        """
        now = datetime.now()
        target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

        if target <= now:
            target += timedelta(days=1)

        self.lock_enabled = True
        self.lock_mode = LockMode.TARGET_TIME
        self.lock_start_time = time.time()
        self.lock_end_time = target.timestamp()
        self.lock_duration = int((self.lock_end_time - self.lock_start_time) / 60)

        print(f"[INFO] Target time lock attivato: fino alle {target_hour:02d}:{target_minute:02d}")
        return True

    def is_locked(self) -> bool:
        """
        Verifica se il blocco è attivo.

        Returns:
            True se ancora in lock, False se scaduto o disabilitato
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
        """
        Calcola tempo rimanente.

        Returns:
            Tuple (minuti, secondi) rimanenti
        """
        if not self.is_locked():
            return (0, 0)

        remaining_seconds = int(self.lock_end_time - time.time())
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60

        return (minutes, seconds)

    def get_progress_percentage(self) -> float:
        """
        Calcola percentuale completamento.

        Returns:
            Percentuale 0-100
        """
        if not self.is_locked() or not self.lock_start_time:
            return 100.0

        total_duration = self.lock_end_time - self.lock_start_time
        elapsed = time.time() - self.lock_start_time

        return min(100.0, (elapsed / total_duration) * 100)

    def clear_lock(self):
        """Rimuove il lock."""
        self.lock_enabled = False
        self.lock_mode = LockMode.NONE
        self.lock_end_time = None
        self.lock_duration = None
        self.lock_start_time = None

        print("[INFO] Focus lock rimosso")

    def force_unlock(self, password: Optional[str] = None) -> bool:
        """
        Sblocco forzato con password (opzionale).

        Args:
            password: Password per sblocco (None = conferma)

        Returns:
            True se sbloccato
        """
        if password is None:
            print("[WARNING] Force unlock richiesto")
            self.clear_lock()
            return True

        return False

    def get_lock_info(self) -> dict:
        """
        Ritorna informazioni sul lock corrente.

        Returns:
            Dict con stato lock
        """
        if not self.is_locked():
            return {
                "locked": False,
                "mode": "none",
                "remaining_time": "00:00"
            }

        minutes, seconds = self.get_remaining_time()

        return {
            "locked": True,
            "mode": self.lock_mode.value,
            "duration_minutes": self.lock_duration,
            "remaining_time": f"{minutes:02d}:{seconds:02d}",
            "remaining_minutes": minutes,
            "remaining_seconds": seconds,
            "progress_percentage": self.get_progress_percentage(),
            "end_time": datetime.fromtimestamp(self.lock_end_time).strftime("%H:%M:%S")
        }


focus_lock = FocusLock()
