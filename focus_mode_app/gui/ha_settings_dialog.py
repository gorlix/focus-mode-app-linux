"""
gui/ha_settings_dialog.py
Dialog modale per la configurazione dell'integrazione con Home Assistant.

Flusso:
  1. L'utente inserisce l'URL di HA e il LLAT, poi clicca "Salva".
  2. Clicca "Registra" per registrare il dispositivo su HA.
  3. Il Webhook ID appare nel campo read-only.
  4. L'utente copia il Webhook ID e lo incolla nella config flow del plugin HACS.
"""

import threading

import ttkbootstrap as ttk

from focus_mode_app.core.ha_config import load_ha_config, save_ha_config, save_webhook_id
from focus_mode_app.gui.material_theme import set_window_center


class HASettingsDialog(ttk.Toplevel):
    """Dialog modale per la configurazione HA (native app model)."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Impostazioni Home Assistant")
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)
        set_window_center(self, 520, 380)

        self._llat_visible = False
        self._build()
        self._load_saved_config()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build(self):
        outer = ttk.Frame(self, padding=16)
        outer.pack(fill="both", expand=True)

        self._build_ha_url_section(outer)
        self._build_llat_section(outer)
        self._build_webhook_section(outer)
        self._build_actions(outer)

        self._feedback_label = ttk.Label(outer, text="", font=("Roboto", 10))
        self._feedback_label.pack(pady=(6, 0))

    def _build_ha_url_section(self, parent):
        frame = ttk.Labelframe(
            parent,
            text="URL di Home Assistant",
            bootstyle="info",
            padding=12,
        )
        frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            frame,
            text="es: https://homeassistant.local:8123  oppure  https://home.esempio.it",
            font=("Roboto", 9),
            foreground="gray",
        ).pack(anchor="w", pady=(0, 4))

        self._ha_url_var = ttk.StringVar()
        ttk.Entry(frame, textvariable=self._ha_url_var).pack(fill="x")

    def _build_llat_section(self, parent):
        frame = ttk.Labelframe(
            parent,
            text="Long-Lived Access Token HA (LLAT)",
            bootstyle="warning",
            padding=12,
        )
        frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            frame,
            text="HA → Profilo → Sicurezza → Token di lunga durata",
            font=("Roboto", 9),
            foreground="gray",
        ).pack(anchor="w", pady=(0, 4))

        row = ttk.Frame(frame)
        row.pack(fill="x")

        self._llat_var = ttk.StringVar()
        self._llat_entry = ttk.Entry(row, textvariable=self._llat_var, show="*")
        self._llat_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self._llat_toggle_btn = ttk.Button(
            row,
            text="Mostra",
            command=self._toggle_llat_visibility,
            bootstyle="warning-outline",
        )
        self._llat_toggle_btn.pack(side="right")

    def _build_webhook_section(self, parent):
        frame = ttk.Labelframe(
            parent,
            text="Webhook ID (generato dopo la registrazione)",
            bootstyle="secondary",
            padding=12,
        )
        frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            frame,
            text="Copia questo ID nel config flow del plugin HACS su Home Assistant.",
            font=("Roboto", 9),
            foreground="gray",
        ).pack(anchor="w", pady=(0, 4))

        row = ttk.Frame(frame)
        row.pack(fill="x")

        self._webhook_id_var = ttk.StringVar()
        ttk.Entry(
            row,
            textvariable=self._webhook_id_var,
            state="readonly",
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        self._copy_btn = ttk.Button(
            row,
            text="Copia",
            command=self._copy_webhook_id,
            bootstyle="secondary",
        )
        self._copy_btn.pack(side="right")

    def _build_actions(self, parent):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(4, 0))

        ttk.Button(
            row,
            text="Salva",
            command=self._save,
            bootstyle="success",
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        self._register_btn = ttk.Button(
            row,
            text="Registra dispositivo",
            command=self._register,
            bootstyle="primary",
        )
        self._register_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))

        ttk.Button(
            row,
            text="Chiudi",
            command=self.destroy,
            bootstyle="secondary",
        ).pack(side="right", expand=True, fill="x")

    # ------------------------------------------------------------------
    # Load / save
    # ------------------------------------------------------------------

    def _load_saved_config(self):
        cfg = load_ha_config()
        self._ha_url_var.set(cfg.get("ha_url", ""))
        self._llat_var.set(cfg.get("llat", ""))
        self._webhook_id_var.set(cfg.get("webhook_id", ""))

    def _save(self):
        ha_url = self._ha_url_var.get().strip()
        llat = self._llat_var.get().strip()
        if save_ha_config(llat=llat, ha_url=ha_url):
            self._show_feedback("Configurazione salvata.")
        else:
            self._show_feedback("Errore durante il salvataggio.")

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def _register(self):
        ha_url = self._ha_url_var.get().strip()
        llat = self._llat_var.get().strip()

        if not ha_url or not llat:
            self._show_feedback("Inserisci URL HA e LLAT prima di registrare.")
            return

        self._register_btn.config(state="disabled", text="Registrazione...")
        self._show_feedback("Connessione a Home Assistant...")

        threading.Thread(
            target=self._do_register,
            args=(ha_url, llat),
            daemon=True,
        ).start()

    def _do_register(self, ha_url: str, llat: str):
        """Runs in a background thread — calls HA API then updates GUI."""
        from focus_mode_app.core.ha_client import HAClient

        try:
            client = HAClient(ha_url=ha_url, llat=llat)
            webhook_id = client.register_device()
            save_ha_config(llat=llat, ha_url=ha_url, webhook_id=webhook_id)
            self.after(0, self._on_register_success, webhook_id)
        except Exception as exc:
            self.after(0, self._on_register_error, str(exc))

    def _on_register_success(self, webhook_id: str):
        self._webhook_id_var.set(webhook_id)
        self._register_btn.config(state="normal", text="Registra dispositivo")
        self._show_feedback(f"Registrato! Copia il Webhook ID nel plugin HACS.", 4000)

    def _on_register_error(self, error: str):
        self._register_btn.config(state="normal", text="Registra dispositivo")
        self._show_feedback(f"Errore: {error}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _copy_webhook_id(self):
        wid = self._webhook_id_var.get()
        if not wid:
            return
        self.clipboard_clear()
        self.clipboard_append(wid)
        self._copy_btn.config(text="Copiato!")
        self.after(1500, lambda: self._copy_btn.config(text="Copia"))

    def _toggle_llat_visibility(self):
        self._llat_visible = not self._llat_visible
        self._llat_entry.config(show="" if self._llat_visible else "*")
        self._llat_toggle_btn.config(
            text="Nascondi" if self._llat_visible else "Mostra"
        )

    def _show_feedback(self, message: str, duration_ms: int = 2500):
        self._feedback_label.config(text=message)
        self.after(duration_ms, lambda: self._feedback_label.config(text=""))
