"""
gui/ha_settings_dialog.py
Pannello inline per configurare l'integrazione con Home Assistant.

Si embedded nella finestra principale come Labelframe collassabile.
Non è una finestra separata — appare/scompare dentro la stessa GUI.

Campi:
  - URL di Home Assistant
  - Long-Lived Access Token (LLAT)
  - Webhook ID (read-only, generato dopo "Registra")
"""

import logging
import uuid
import tkinter as tk
from tkinter import ttk

_LOGGER = logging.getLogger(__name__)


class HASettingsPanel:
    """
    Pannello HA da embeddare in un frame parent.
    Chiama build(parent) per costruire i widget.
    """

    def __init__(self, parent: tk.Widget):
        self._parent = parent
        self._frame = ttk.LabelFrame(
            parent, text="Impostazioni Home Assistant", padding=12
        )
        self._build()
        self._load()

    @property
    def frame(self) -> ttk.LabelFrame:
        return self._frame

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build(self):
        f = self._frame

        # ── URL HA ────────────────────────────────────────────────────
        ttk.Label(f, text="URL di Home Assistant:").grid(
            row=0, column=0, sticky="w", pady=(0, 2)
        )
        self._url_var = tk.StringVar()
        ttk.Entry(f, textvariable=self._url_var, width=42).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(0, 2)
        )
        ttk.Label(
            f, text="es: https://homeassistant.local:8123", foreground="gray"
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # ── LLAT ──────────────────────────────────────────────────────
        ttk.Label(f, text="Long-Lived Access Token (LLAT):").grid(
            row=3, column=0, sticky="w", pady=(0, 2)
        )
        llat_frame = ttk.Frame(f)
        llat_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 2))
        self._llat_var = tk.StringVar()
        self._llat_entry = ttk.Entry(llat_frame, textvariable=self._llat_var, show="*")
        self._llat_entry.pack(side="left", fill="x", expand=True)
        self._show_btn = ttk.Button(
            llat_frame, text="Mostra", width=8, command=self._toggle_llat
        )
        self._show_btn.pack(side="left", padx=(6, 0))

        ttk.Label(
            f,
            text="HA → Profilo → Sicurezza → Token di lunga durata",
            foreground="gray",
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # ── Webhook ID ────────────────────────────────────────────────
        ttk.Label(f, text="Webhook ID:").grid(row=6, column=0, sticky="w", pady=(0, 2))
        wh_frame = ttk.Frame(f)
        wh_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0, 2))
        self._wh_var = tk.StringVar()
        ttk.Entry(
            wh_frame, textvariable=self._wh_var, state="readonly", foreground="blue"
        ).pack(side="left", fill="x", expand=True)
        ttk.Button(wh_frame, text="Copia", width=8, command=self._copy_wh).pack(
            side="left", padx=(6, 0)
        )
        ttk.Label(
            f,
            text="Incolla nel config flow del plugin HACS su Home Assistant.",
            foreground="gray",
        ).grid(row=8, column=0, columnspan=2, sticky="w", pady=(0, 14))

        # ── Salva (riga dedicata, piena larghezza) ────────────────────
        ttk.Button(
            f,
            text="Salva configurazione",
            command=self._save,
        ).grid(row=9, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        # ── Rigenera Webhook ID ───────────────────────────────────────
        ttk.Button(
            f,
            text="Rigenera Webhook ID",
            command=self._regen_webhook,
        ).grid(row=10, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        # ── Feedback ─────────────────────────────────────────────────
        self._feedback_var = tk.StringVar()
        self._feedback_lbl = ttk.Label(
            f, textvariable=self._feedback_var, foreground="#388E3C"
        )
        self._feedback_lbl.grid(row=11, column=0, columnspan=2, sticky="w", pady=(0, 2))

        f.columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # Load / save
    # ------------------------------------------------------------------

    def _load(self):
        from focus_mode_app.core.ha_config import load_ha_config

        cfg = load_ha_config()
        self._url_var.set(cfg.get("ha_url", ""))
        self._llat_var.set(cfg.get("llat", ""))
        self._wh_var.set(cfg.get("webhook_id", ""))
        _LOGGER.debug(
            "Panel loaded: ha_url=%s webhook_id=%s",
            cfg.get("ha_url") or "(empty)",
            cfg.get("webhook_id") or "(empty)",
        )

    def _save(self):
        from focus_mode_app.core.ha_config import save_ha_config

        ha_url = self._url_var.get().strip()
        llat = self._llat_var.get().strip()
        _LOGGER.info(
            "Save requested: ha_url=%s llat=%s",
            ha_url or "(empty)",
            "***" if llat else "(empty)",
        )
        if not ha_url or not llat:
            self._msg("Inserisci URL e Token prima di salvare.", error=True)
            _LOGGER.warning("Save aborted: missing ha_url or llat")
            return
        # Auto-generate webhook_id on first save if not already present.
        webhook_id = self._wh_var.get().strip()
        if not webhook_id:
            webhook_id = str(uuid.uuid4()).replace("-", "")
            self._wh_var.set(webhook_id)
            _LOGGER.info("Auto-generated webhook_id: %s", webhook_id)
        if save_ha_config(llat=llat, ha_url=ha_url, webhook_id=webhook_id):
            self._msg("Configurazione salvata.")
            _LOGGER.info("Settings saved OK")
        else:
            self._msg("Errore durante il salvataggio.", error=True)
            _LOGGER.error("Settings save FAILED")

    # ------------------------------------------------------------------
    # Webhook ID management
    # ------------------------------------------------------------------

    def _regen_webhook(self):
        """Generate a brand-new webhook ID (e.g. after re-installing HACS)."""
        new_id = str(uuid.uuid4()).replace("-", "")
        self._wh_var.set(new_id)
        self._msg("Nuovo Webhook ID generato. Salvare e aggiornare il plugin HACS.")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _toggle_llat(self):
        showing = self._llat_entry.cget("show") == ""
        self._llat_entry.config(show="*" if showing else "")
        self._show_btn.config(text="Mostra" if showing else "Nascondi")

    def _copy_wh(self):
        wid = self._wh_var.get()
        if not wid:
            return
        self._frame.clipboard_clear()
        self._frame.clipboard_append(wid)
        self._msg("Webhook ID copiato negli appunti.")
        _LOGGER.debug("Webhook ID copied to clipboard: %s", wid)

    def _msg(self, text: str, error: bool = False):
        self._feedback_var.set(text)
        self._feedback_lbl.config(foreground="#D32F2F" if error else "#388E3C")
        self._frame.after(3000, lambda: self._feedback_var.set(""))
