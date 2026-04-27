"""
gui/ha_settings_dialog.py
Popup per configurare l'integrazione con Home Assistant.

Chiede due cose all'utente:
  1. URL di Home Assistant (es. https://homeassistant.local:8123)
  2. Long-Lived Access Token (LLAT)

Il tasto "Salva" persiste la config; il tasto "Registra" chiama
register_device() e mostra il Webhook ID da incollare nel plugin HACS.

Usa composizione (owns a Toplevel) invece di ereditarietà per evitare
un bug di ttkbootstrap che patcha tk.Toplevel.__init__ e rompe _register.
"""

import threading
import tkinter as tk
from tkinter import font as tkfont


class HASettingsDialog:
    """Popup modale per la configurazione HA (non eredita da Toplevel)."""

    def __init__(self, parent):
        win = tk.Toplevel(parent)
        win.title("Impostazioni Home Assistant")
        win.resizable(False, False)
        win.grab_set()
        win.transient(parent)

        # Centra rispetto al parent
        w, h = 480, 360
        px = parent.winfo_rootx() + max(0, (parent.winfo_width() - w) // 2)
        py = parent.winfo_rooty() + max(0, (parent.winfo_height() - h) // 2)
        win.geometry(f"{w}x{h}+{px}+{py}")

        self._win = win
        self._build(win)
        self._load()

    # Proxy per winfo_exists() usato da main_window.py
    def winfo_exists(self) -> bool:
        try:
            return bool(self._win.winfo_exists())
        except Exception:
            return False

    def lift(self):
        self._win.lift()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build(self, win):
        bold = tkfont.Font(weight="bold")
        pad = dict(padx=12, pady=4)

        outer = tk.Frame(win, padx=16, pady=16)
        outer.pack(fill="both", expand=True)

        # ── URL HA ────────────────────────────────────────────────────
        tk.Label(outer, text="URL di Home Assistant:", font=bold).pack(anchor="w")
        tk.Label(
            outer,
            text="es: https://homeassistant.local:8123",
            fg="gray",
        ).pack(anchor="w")
        self._url_var = tk.StringVar()
        tk.Entry(outer, textvariable=self._url_var, width=56).pack(fill="x", **pad)

        # ── LLAT ──────────────────────────────────────────────────────
        tk.Label(
            outer, text="Long-Lived Access Token (LLAT):", font=bold
        ).pack(anchor="w", pady=(10, 0))
        tk.Label(
            outer,
            text="HA → Profilo → Sicurezza → Token di lunga durata",
            fg="gray",
        ).pack(anchor="w")

        llat_row = tk.Frame(outer)
        llat_row.pack(fill="x", **pad)
        self._llat_var = tk.StringVar()
        self._llat_entry = tk.Entry(llat_row, textvariable=self._llat_var, show="*", width=47)
        self._llat_entry.pack(side="left", fill="x", expand=True)
        self._show_btn = tk.Button(
            llat_row, text="Mostra", command=self._toggle_llat, width=8
        )
        self._show_btn.pack(side="right", padx=(6, 0))

        # ── Webhook ID ────────────────────────────────────────────────
        tk.Label(outer, text="Webhook ID:", font=bold).pack(
            anchor="w", pady=(10, 0)
        )
        wh_row = tk.Frame(outer)
        wh_row.pack(fill="x", **pad)
        self._wh_var = tk.StringVar()
        tk.Entry(
            wh_row,
            textvariable=self._wh_var,
            state="readonly",
            fg="blue",
            width=47,
        ).pack(side="left", fill="x", expand=True)
        tk.Button(wh_row, text="Copia", command=self._copy_wh, width=8).pack(
            side="right", padx=(6, 0)
        )
        tk.Label(
            outer,
            text="Copia nel config flow del plugin HACS su Home Assistant.",
            fg="gray",
        ).pack(anchor="w")

        # ── Pulsanti ─────────────────────────────────────────────────
        btn_row = tk.Frame(outer)
        btn_row.pack(fill="x", pady=(14, 0))

        tk.Button(
            btn_row, text="Salva", command=self._save,
            bg="#4CAF50", fg="white", width=12,
        ).pack(side="left", padx=(0, 6))

        self._reg_btn = tk.Button(
            btn_row, text="Registra", command=self._register,
            bg="#2196F3", fg="white", width=14,
        )
        self._reg_btn.pack(side="left", padx=(0, 6))

        tk.Button(
            btn_row, text="Chiudi", command=win.destroy, width=10
        ).pack(side="right")

        # ── Feedback ─────────────────────────────────────────────────
        self._feedback_var = tk.StringVar()
        self._feedback_lbl = tk.Label(
            outer, textvariable=self._feedback_var, fg="#388E3C"
        )
        self._feedback_lbl.pack(pady=(8, 0))

    # ------------------------------------------------------------------
    # Load / save
    # ------------------------------------------------------------------

    def _load(self):
        from focus_mode_app.core.ha_config import load_ha_config
        cfg = load_ha_config()
        self._url_var.set(cfg.get("ha_url", ""))
        self._llat_var.set(cfg.get("llat", ""))
        self._wh_var.set(cfg.get("webhook_id", ""))

    def _save(self):
        from focus_mode_app.core.ha_config import save_ha_config
        ha_url = self._url_var.get().strip()
        llat = self._llat_var.get().strip()
        if not ha_url or not llat:
            self._msg("Inserisci URL e Token prima di salvare.", error=True)
            return
        if save_ha_config(llat=llat, ha_url=ha_url):
            self._msg("Configurazione salvata.")
        else:
            self._msg("Errore durante il salvataggio.", error=True)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def _register(self):
        ha_url = self._url_var.get().strip()
        llat = self._llat_var.get().strip()
        if not ha_url or not llat:
            self._msg("Inserisci URL e Token prima di registrare.", error=True)
            return
        self._reg_btn.config(state="disabled", text="Registrazione…")
        self._msg("Connessione a Home Assistant…")
        threading.Thread(
            target=self._do_register, args=(ha_url, llat), daemon=True
        ).start()

    def _do_register(self, ha_url: str, llat: str):
        from focus_mode_app.core.ha_client import HAClient
        from focus_mode_app.core.ha_config import save_ha_config
        try:
            client = HAClient(ha_url=ha_url, llat=llat)
            webhook_id = client.register_device()
            save_ha_config(llat=llat, ha_url=ha_url, webhook_id=webhook_id)
            self._win.after(0, self._on_ok, webhook_id)
        except Exception as exc:
            self._win.after(0, self._on_err, str(exc))

    def _on_ok(self, webhook_id: str):
        self._wh_var.set(webhook_id)
        self._reg_btn.config(state="normal", text="Registra")
        self._msg("Registrato! Copia il Webhook ID nel plugin HACS.")

    def _on_err(self, error: str):
        self._reg_btn.config(state="normal", text="Registra")
        self._msg(f"Errore: {error}", error=True)

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
        self._win.clipboard_clear()
        self._win.clipboard_append(wid)
        self._msg("Webhook ID copiato negli appunti.")

    def _msg(self, text: str, error: bool = False):
        self._feedback_var.set(text)
        self._feedback_lbl.config(fg="#D32F2F" if error else "#388E3C")
        self._win.after(3000, lambda: self._feedback_var.set(""))
