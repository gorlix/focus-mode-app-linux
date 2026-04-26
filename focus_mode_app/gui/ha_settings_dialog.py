"""
gui/ha_settings_dialog.py
Dialog modale per la configurazione dell'integrazione con Home Assistant.

Espone tre sezioni:
  1. Token Bearer dell'app (read-only, copiabile) — necessario per configurare
     il plugin HACS o i rest_command di HA verso questa app.
  2. URL webhook dying gasp — inviato da questa app a HA allo spegnimento.
  3. URL webhook eventi di stato — inviato da questa app a HA ad ogni cambio
     di stato (attiva/disattiva, lock, restore).
  4. Long-Lived Access Token HA — memorizzato per uso futuro da parte dell'app
     verso le API di Home Assistant.
"""

import ttkbootstrap as ttk

from focus_mode_app.api.config import API_AUTH_TOKEN_FILE
from focus_mode_app.core.ha_config import load_ha_config, save_ha_config
from focus_mode_app.gui.material_theme import set_window_center


class HASettingsDialog(ttk.Toplevel):
    """
    Dialog modale per la configurazione dell'integrazione Home Assistant.
    Si apre come finestra figlia della GUI principale ed è bloccante
    (grab_set) finché l'utente non chiude o salva.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Impostazioni Home Assistant")
        self.resizable(False, False)
        self.grab_set()       # modale — blocca interazione con la finestra padre
        self.transient(parent)

        set_window_center(self, 520, 460)

        self._llat_visible = False
        self._build()
        self._load_saved_config()

    # ======================================================================
    # COSTRUZIONE WIDGET
    # ======================================================================

    def _build(self):
        """Costruisce l'intera interfaccia del dialog."""
        outer = ttk.Frame(self, padding=16)
        outer.pack(fill="both", expand=True)

        self._build_token_section(outer)
        self._build_dying_gasp_section(outer)
        self._build_state_event_section(outer)
        self._build_llat_section(outer)
        self._build_actions(outer)

        self._feedback_label = ttk.Label(outer, text="", font=("Roboto", 10))
        self._feedback_label.pack(pady=(6, 0))

    def _build_token_section(self, parent):
        """
        Sezione read-only con il Bearer token dell'app.
        L'utente copia questo token nella configurazione di HA (plugin HACS o rest_command).
        """
        frame = ttk.Labelframe(
            parent,
            text="Token App (HA → Linux)",
            bootstyle="secondary",
            padding=12
        )
        frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            frame,
            text="Inserisci questo token nel plugin HACS o nei rest_command di HA:",
            font=("Roboto", 10)
        ).pack(anchor="w", pady=(0, 6))

        row = ttk.Frame(frame)
        row.pack(fill="x")

        token_value = self._read_app_token()
        self._token_var = ttk.StringVar(value=token_value)

        token_entry = ttk.Entry(row, textvariable=self._token_var, state="readonly")
        token_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self._copy_btn = ttk.Button(row, text="Copia", command=self._copy_token, bootstyle="secondary")
        self._copy_btn.pack(side="right")

    def _build_dying_gasp_section(self, parent):
        """
        Sezione per configurare l'URL del webhook dying gasp.
        Questo webhook viene chiamato dall'app a HA solo allo spegnimento.
        """
        frame = ttk.Labelframe(
            parent,
            text="Webhook Dying Gasp (app → HA allo spegnimento)",
            bootstyle="info",
            padding=12
        )
        frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            frame,
            text="es: https://home.alessandrogorla.it/api/webhook/linux_focus_mode_offline",
            font=("Roboto", 9),
            foreground="gray"
        ).pack(anchor="w", pady=(0, 4))

        self._dying_gasp_var = ttk.StringVar()
        ttk.Entry(frame, textvariable=self._dying_gasp_var).pack(fill="x")

    def _build_state_event_section(self, parent):
        """
        Sezione per configurare l'URL del webhook eventi di stato.
        Viene chiamato dall'app ogni volta che lo stato cambia (focus on/off, lock, restore).
        """
        frame = ttk.Labelframe(
            parent,
            text="Webhook Eventi di Stato (app → HA, real-time)",
            bootstyle="info",
            padding=12
        )
        frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            frame,
            text="es: https://home.alessandrogorla.it/api/webhook/linux_focus_mode",
            font=("Roboto", 9),
            foreground="gray"
        ).pack(anchor="w", pady=(0, 4))

        self._state_event_var = ttk.StringVar()
        ttk.Entry(frame, textvariable=self._state_event_var).pack(fill="x")

    def _build_llat_section(self, parent):
        """
        Sezione per il Long-Lived Access Token HA.
        Conservato per uso futuro da parte dell'app per chiamare le API di HA.
        """
        frame = ttk.Labelframe(
            parent,
            text="Long-Lived Access Token HA (LLAT)",
            bootstyle="warning",
            padding=12
        )
        frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            frame,
            text="Token generato in HA → Profilo → Token di lunga durata",
            font=("Roboto", 9),
            foreground="gray"
        ).pack(anchor="w", pady=(0, 4))

        row = ttk.Frame(frame)
        row.pack(fill="x")

        self._llat_var = ttk.StringVar()
        self._llat_entry = ttk.Entry(row, textvariable=self._llat_var, show="*")
        self._llat_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self._llat_toggle_btn = ttk.Button(
            row, text="Mostra", command=self._toggle_llat_visibility, bootstyle="warning-outline"
        )
        self._llat_toggle_btn.pack(side="right")

    def _build_actions(self, parent):
        """Riga con i pulsanti Salva e Chiudi."""
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(4, 0))

        ttk.Button(
            row, text="Salva", command=self._save, bootstyle="success"
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        ttk.Button(
            row, text="Chiudi", command=self.destroy, bootstyle="secondary"
        ).pack(side="right", expand=True, fill="x")

    # ======================================================================
    # CARICAMENTO DATI
    # ======================================================================

    def _read_app_token(self) -> str:
        """Legge il Bearer token dell'app da disco. Ritorna stringa vuota in caso di errore."""
        try:
            return API_AUTH_TOKEN_FILE.read_text(encoding="utf-8").strip()
        except OSError:
            return "(token non disponibile)"

    def _load_saved_config(self):
        """Popola i campi del dialog con i valori salvati in ha_config.json."""
        config = load_ha_config()
        self._dying_gasp_var.set(config.get("dying_gasp_url", ""))
        self._state_event_var.set(config.get("state_event_url", ""))
        self._llat_var.set(config.get("llat", ""))

    # ======================================================================
    # AZIONI
    # ======================================================================

    def _copy_token(self):
        """Copia il Bearer token negli appunti di sistema e conferma visivamente."""
        token = self._token_var.get()
        self.clipboard_clear()
        self.clipboard_append(token)
        self._copy_btn.config(text="Copiato!")
        self.after(1500, lambda: self._copy_btn.config(text="Copia"))

    def _toggle_llat_visibility(self):
        """Alterna la visibilità del campo LLAT tra testo e asterischi."""
        self._llat_visible = not self._llat_visible
        if self._llat_visible:
            self._llat_entry.config(show="")
            self._llat_toggle_btn.config(text="Nascondi")
        else:
            self._llat_entry.config(show="*")
            self._llat_toggle_btn.config(text="Mostra")

    def _save(self):
        """Salva la configurazione HA su disco e mostra il feedback."""
        dying_gasp = self._dying_gasp_var.get().strip()
        state_event = self._state_event_var.get().strip()
        llat = self._llat_var.get().strip()

        if save_ha_config(dying_gasp, state_event, llat):
            self._show_feedback("Configurazione salvata.")
        else:
            self._show_feedback("Errore durante il salvataggio.")

    def _show_feedback(self, message: str, duration_ms: int = 2500):
        """Mostra un messaggio temporaneo nella riga di feedback del dialog."""
        self._feedback_label.config(text=message)
        self.after(duration_ms, lambda: self._feedback_label.config(text=""))
