"""
gui/main_window.py
Finestra principale dell'applicazione Focus Mode App.
Gestisce l'interfaccia utente per configurare app e webapp da bloccare.
Integra pannello di gestione app da ripristinare automaticamente.
Integra focus lock timer e target time per impedire disattivazione prematura.
"""

from tkinter import messagebox
import ttkbootstrap as ttk

from config import WINDOW_WIDTH, WINDOW_HEIGHT, GUI_THEME, APP_TITLE
from core.blocker import (
    is_blocking_active,
    toggle_blocking,
    set_restore_enabled,
    is_restore_enabled,
    can_disable_blocking
)
from core.storage import (
    add_blocked_item,
    remove_blocked_item,
    get_blocked_items
)
from utils.tray_icon import update_tray_menu
from gui.material_theme import (
    apply_material3_style,
    material_label,
    material_entry,
    material_button,
    material_listbox,
    create_card_frame,
    set_window_center,
    MaterialColors
)


class AppGui(ttk.Window):
    """
    Finestra principale dell'applicazione Focus Mode App.
    Gestisce l'interfaccia utente per configurare app e webapp da bloccare.
    Include pannello di gestione app da ripristinare.
    Include focus lock timer e target time per sessioni concentrate.
    """

    def __init__(self):
        """Inizializza la finestra principale con tema e layout Material 3."""
        super().__init__(themename=GUI_THEME)

        self.title(APP_TITLE)

        set_window_center(self, WINDOW_WIDTH, WINDOW_HEIGHT)

        apply_material3_style(self)

        self._create_widgets()

        self.refresh_list()

        self.protocol("WM_DELETE_WINDOW", self.hide_window)

    # ========================================================================
    # CREAZIONE INTERFACCIA
    # ========================================================================

    def _create_widgets(self):
        """Crea tutti i widget dell'interfaccia principale."""
        main_frame = create_card_frame(self, padx=24, pady=24)

        self._create_title(main_frame)
        self._create_toggle_button(main_frame)
        self._create_timer_panel(main_frame)
        self._create_restore_panel(main_frame)
        self._create_blocked_section(main_frame)
        self._create_feedback_label(main_frame)
        self._create_action_buttons(main_frame)

    def _create_title(self, parent):
        """Crea il titolo principale dell'interfaccia."""
        title = material_label(parent, "Focus Mode App", style_type="title")
        title.pack(pady=(0, 10))

    def _create_toggle_button(self, parent):
        """Crea il bottone toggle per attivare/disattivare il blocco."""
        self.toggle_btn = ttk.Button(
            parent,
            text="ATTIVA MODALITÀ STUDIO",
            command=self.toggle_blocking,
            bootstyle="success-outline",
            width=30
        )
        self.toggle_btn.pack(pady=(0, 20))

    def _create_timer_panel(self, parent):
        """
        Crea pannello timer/target time per focus lock.
        Permette di impostare timer countdown o ora target.
        """
        timer_frame = ttk.LabelFrame(
            parent,
            text="FOCUS LOCK",
            bootstyle="warning",
            padding=16
        )
        timer_frame.pack(fill="x", pady=(0, 16))

        # Radio buttons per scegliere modalità
        mode_frame = ttk.Frame(timer_frame)
        mode_frame.pack(fill="x", pady=(0, 8))

        self.lock_mode = ttk.StringVar(value="timer")

        radio_timer = ttk.Radiobutton(
            mode_frame,
            text="⏲️ Timer (minuti)",
            variable=self.lock_mode,
            value="timer",
            bootstyle="warning",
            command=self.update_lock_input_visibility
        )
        radio_timer.pack(side="left", padx=(0, 16))

        radio_target = ttk.Radiobutton(
            mode_frame,
            text="🕐 Fino alle ore",
            variable=self.lock_mode,
            value="target",
            bootstyle="warning",
            command=self.update_lock_input_visibility
        )
        radio_target.pack(side="left")

        # Frame timer input
        self.timer_input_frame = ttk.Frame(timer_frame)
        self.timer_input_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(self.timer_input_frame, text="Minuti:").pack(side="left", padx=(0, 8))

        self.timer_entry = ttk.Entry(self.timer_input_frame, width=10)
        self.timer_entry.pack(side="left", padx=(0, 8))
        self.timer_entry.insert(0, "25")

        # Frame target time input
        self.target_input_frame = ttk.Frame(timer_frame)

        ttk.Label(self.target_input_frame, text="Ora:").pack(side="left", padx=(0, 8))

        self.target_hour_entry = ttk.Entry(self.target_input_frame, width=5)
        self.target_hour_entry.pack(side="left", padx=(0, 4))
        self.target_hour_entry.insert(0, "14")

        ttk.Label(self.target_input_frame, text=":").pack(side="left", padx=2)

        self.target_minute_entry = ttk.Entry(self.target_input_frame, width=5)
        self.target_minute_entry.pack(side="left", padx=(4, 8))
        self.target_minute_entry.insert(0, "30")

        ttk.Label(self.target_input_frame, text="(HH:MM)").pack(side="left", padx=(0, 8))

        # Bottone attiva lock
        self.btn_activate_lock = material_button(
            timer_frame,
            "Attiva Lock",
            self.activate_lock,
            button_type="warning"
        )
        self.btn_activate_lock.pack(fill="x", pady=(0, 8))

        # Status label
        self.timer_status_label = ttk.Label(
            timer_frame,
            text="Nessun lock attivo",
            font=("Roboto", 11, "bold"),
            foreground="gray"
        )
        self.timer_status_label.pack()

        # Imposta visibilità iniziale
        self.update_lock_input_visibility()

        # Avvia update loop
        self.update_timer_display()

    def update_lock_input_visibility(self):
        """Mostra/nasconde input in base alla modalità selezionata."""
        if self.lock_mode.get() == "timer":
            self.timer_input_frame.pack(fill="x", pady=(0, 8))
            self.target_input_frame.pack_forget()
        else:
            self.timer_input_frame.pack_forget()
            self.target_input_frame.pack(fill="x", pady=(0, 8))

    def activate_lock(self):
        """Attiva focus lock in modalità timer o target time."""
        try:
            from core.focus_lock import focus_lock

            mode = self.lock_mode.get()

            if mode == "timer":
                minutes = int(self.timer_entry.get())

                if minutes <= 0:
                    self.show_feedback("Inserisci minuti > 0")
                    return

                if focus_lock.set_timer_lock(minutes):
                    self.show_feedback(f"Timer Lock attivato: {minutes} min")
                else:
                    self.show_feedback("Errore attivazione timer")
                    return

            else:
                hour = int(self.target_hour_entry.get())
                minute = int(self.target_minute_entry.get())

                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    self.show_feedback("Ora non valida (HH: 0-23, MM: 0-59)")
                    return

                if focus_lock.set_target_time_lock(hour, minute):
                    self.show_feedback(f"Target Time Lock: {hour:02d}:{minute:02d}")
                else:
                    self.show_feedback("Errore attivazione target time")
                    return

            if not is_blocking_active():
                toggle_blocking()
                self.update_toggle_button()

        except ValueError:
            self.show_feedback("Inserisci valori numerici validi")
        except Exception as e:
            self.show_feedback(f"Errore: {e}")

    def update_timer_display(self):
        """
        Aggiorna display timer ogni secondo.
        Mostra countdown e gestisce stato bottone disattiva.
        """
        try:
            from core.focus_lock import focus_lock

            if focus_lock.is_locked():
                info = focus_lock.get_lock_info()
                self.timer_status_label.config(
                    text=f"LOCKED - {info['remaining_time']} rimanenti",
                    foreground="red"
                )

                if is_blocking_active():
                    self.toggle_btn.config(state="disabled")
            else:
                self.timer_status_label.config(
                    text="Nessun lock attivo",
                    foreground="gray"
                )

                self.toggle_btn.config(state="normal")

        except ImportError:
            pass
        except Exception as e:
            print(f"[ERROR] Timer display update: {e}")

        self.after(1000, self.update_timer_display)

    def _create_restore_panel(self, parent):
        """
        Crea il pannello per gestire app da ripristinare automaticamente.
        Permette all'utente di selezionare quali app ripristinare quando
        il blocco viene disattivato.
        """
        restore_frame = ttk.LabelFrame(
            parent,
            text="AUTO-RESTORE ON DISABLE",
            bootstyle="info",
            padding=16
        )
        restore_frame.pack(fill="both", expand=False, pady=(0, 16))

        self.restore_listbox = material_listbox(restore_frame, height=3)
        self.restore_listbox.pack(fill="both", expand=True, pady=(0, 8))

        restore_btn_frame = ttk.Frame(restore_frame)
        restore_btn_frame.pack(fill="x", pady=(0, 8))

        btn_add_restore = material_button(
            restore_btn_frame,
            "Add to Restore",
            self.add_to_restore,
            button_type="info"
        )
        btn_add_restore.pack(side="left", expand=True, fill="x", padx=(0, 4))

        btn_remove_restore = ttk.Button(
            restore_btn_frame,
            text="Remove",
            command=self.remove_from_restore,
            bootstyle="danger"
        )
        btn_remove_restore.pack(side="right", expand=True, fill="x", padx=(4, 0))

        self.restore_toggle_frame = ttk.Frame(restore_frame)
        self.restore_toggle_frame.pack(fill="x")

        self.restore_toggle_btn = ttk.Button(
            self.restore_toggle_frame,
            text="SOSPENDI AUTO-RESTORE",
            command=self.toggle_restore_enabled,
            bootstyle="warning-outline"
        )
        self.restore_toggle_btn.pack(fill="x")

        self.refresh_restore_list()

    def _create_blocked_section(self, parent):
        """Crea la sezione per gestire elementi bloccati (app e webapp)."""
        section = ttk.LabelFrame(
            parent,
            text="Elementi Bloccati",
            bootstyle="primary",
            padding=16
        )
        section.pack(fill="both", expand=True, pady=(0, 16))

        self._create_type_selector(section)

        self.desc_label = material_label(section, "")
        self.desc_label.pack(anchor="w", pady=(0, 8))
        self.update_description()

        self.entry = material_entry(section)
        self.entry.pack(fill="x", pady=(0, 8))

        self._create_item_buttons(section)

        self.listbox = material_listbox(section, height=6)
        self.listbox.pack(fill="both", expand=True)

    def _create_type_selector(self, parent):
        """Crea i radio button per selezionare il tipo (app nativa o webapp)."""
        radio_frame = ttk.Frame(parent)
        radio_frame.pack(fill="x", pady=(0, 12))

        self.item_type = ttk.StringVar(value="app")

        radio_app = ttk.Radiobutton(
            radio_frame,
            text="App Nativa",
            variable=self.item_type,
            value="app",
            bootstyle="primary"
        )
        radio_app.pack(side="left", padx=(0, 16))

        radio_webapp = ttk.Radiobutton(
            radio_frame,
            text="Webapp",
            variable=self.item_type,
            value="webapp",
            bootstyle="info"
        )
        radio_webapp.pack(side="left")

        self.item_type.trace_add("write", lambda *args: self.update_description())

    def _create_item_buttons(self, parent):
        """Crea i bottoni per aggiungere e rimuovere elementi dalla lista."""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", pady=(0, 8))

        btn_add = material_button(
            btn_frame,
            "Aggiungi",
            self.add_item,
            button_type="primary"
        )
        btn_add.pack(side="left", expand=True, fill="x", padx=(0, 4))

        btn_remove = ttk.Button(
            btn_frame,
            text="Rimuovi",
            command=self.remove_item,
            bootstyle="danger"
        )
        btn_remove.pack(side="right", expand=True, fill="x", padx=(4, 0))

    def _create_feedback_label(self, parent):
        """Crea il label per visualizzare messaggi di feedback temporanei."""
        self.feedback_label = ttk.Label(
            parent,
            text="",
            font=("Roboto", 11),
            foreground=MaterialColors.PRIMARY,
            background=MaterialColors.SURFACE
        )
        self.feedback_label.pack(pady=(8, 0))

    def _create_action_buttons(self, parent):
        """Crea i bottoni azioni principali (aggiorna, esci)."""
        actions_frame = ttk.Frame(parent)
        actions_frame.pack(fill="x", pady=(8, 0))

        btn_refresh = material_button(
            actions_frame,
            "Aggiorna",
            self.refresh_list,
            button_type="secondary"
        )
        btn_refresh.pack(side="left", expand=True, fill="x", padx=(0, 4))

        btn_quit = ttk.Button(
            actions_frame,
            text="Esci",
            command=self.quit_app,
            bootstyle="danger"
        )
        btn_quit.pack(side="right", expand=True, fill="x", padx=(4, 0))

    # ========================================================================
    # GESTIONE BLOCCO
    # ========================================================================

    def toggle_blocking(self):
        """
        Attiva/disattiva il blocco e aggiorna l'interfaccia.
        Gestisce anche il ripristino automatico alla disattivazione.
        Controlla focus lock prima di disattivare.
        """
        if is_blocking_active():
            can_disable, reason = can_disable_blocking()
            if not can_disable:
                self.show_feedback(f"{reason}")
                return

        new_state = toggle_blocking()
        self.update_toggle_button()

        update_tray_menu()

    def update_toggle_button(self):
        """Aggiorna il testo e lo stile del bottone toggle in base allo stato."""
        if is_blocking_active():
            self.toggle_btn.config(
                text="DISATTIVA MODALITÀ STUDIO",
                bootstyle="danger"
            )
            self.show_feedback("Modalità Studio ATTIVATA - Le app verranno bloccate")
        else:
            self.toggle_btn.config(
                text="ATTIVA MODALITÀ STUDIO",
                bootstyle="success-outline"
            )
            self.show_feedback("Modalità Studio DISATTIVATA - Nessun blocco attivo")

    # ========================================================================
    # GESTIONE RESTORE
    # ========================================================================

    def add_to_restore(self):
        """
        Aggiunge l'app selezionata dalla lista bloccati alla lista restore.
        Usa get_blocked_items() per sincronizzazione corretta.
        """
        selection = self.listbox.curselection()
        if not selection:
            self.show_feedback("Seleziona un'app prima")
            return

        index = selection[0]
        items = get_blocked_items()

        if index >= len(items):
            print(f"[ERROR] Index {index} out of range (len={len(items)})")
            self.show_feedback("Errore: elemento non trovato")
            self.refresh_list()
            return

        app_name = items[index]["name"]

        try:
            from core.session import session_tracker
            session_tracker.add_to_restore(app_name)
            self.refresh_restore_list()
            self.show_feedback(f"{app_name} aggiunto a restore!")
        except Exception as e:
            print(f"[ERROR] Add to restore: {e}")
            self.show_feedback(f"Errore: {e}")

    def remove_from_restore(self):
        """
        Rimuove l'app selezionata dalla lista restore.
        """
        selection = self.restore_listbox.curselection()
        if not selection:
            self.show_feedback("Seleziona un'app prima")
            return

        try:
            from core.session import session_tracker

            app_names = list(session_tracker.restore_list.keys())
            if selection[0] >= len(app_names):
                self.show_feedback("Errore: elemento non trovato")
                return

            app_name = app_names[selection[0]]

            session_tracker.remove_from_restore(app_name)
            self.refresh_restore_list()
            self.show_feedback(f"{app_name} rimosso da restore!")
        except Exception as e:
            print(f"[ERROR] Remove from restore: {e}")
            self.show_feedback(f"Errore: {e}")

    def refresh_restore_list(self):
        """Aggiorna la listbox con le app da ripristinare."""
        self.restore_listbox.delete(0, ttk.END)

        try:
            from core.session import session_tracker

            for app_name in session_tracker.restore_list.keys():
                self.restore_listbox.insert(ttk.END, f"{app_name}")
        except Exception as e:
            print(f"[ERROR] Refresh restore list: {e}")

    def toggle_restore_enabled(self):
        """
        Toggle lo stato del restore automatico per la sessione corrente.
        Permette all'utente di disabilitare il restore on-the-fly.
        """
        current_state = is_restore_enabled()
        new_state = not current_state

        set_restore_enabled(new_state)

        if new_state:
            self.restore_toggle_btn.config(
                text="SOSPENDI AUTO-RESTORE",
                bootstyle="warning-outline"
            )
            self.show_feedback("Auto-restore ABILITATO")
        else:
            self.restore_toggle_btn.config(
                text="ABILITA AUTO-RESTORE",
                bootstyle="success-outline"
            )
            self.show_feedback("Auto-restore DISABILITATO")

    # ========================================================================
    # GESTIONE ELEMENTI BLOCCATI
    # ========================================================================

    def update_description(self):
        """Aggiorna il testo descrittivo in base al tipo selezionato."""
        if self.item_type.get() == "app":
            self.desc_label.config(text="Nome eseguibile (es: firefox, telegram):")
        else:
            self.desc_label.config(text="URL o stringa comando (es: web.whatsapp.com):")

    def add_item(self):
        """
        Aggiunge un elemento alla lista bloccati.
        Normalizza il nome e lo salva su disco.
        """
        name = self.entry.get().strip()
        item_type = self.item_type.get()

        if item_type == "app":
            name = name.lower()

        if not name:
            self.show_feedback("Inserisci un valore valido")
            return

        if add_blocked_item(name, item_type):
            self.listbox.insert(ttk.END, f"{name}")
            self.show_feedback(f"{name} aggiunto e salvato!")
            self.entry.delete(0, ttk.END)
        else:
            self.show_feedback("Elemento già presente o non valido")

    def remove_item(self):
        """
        Rimuove l'elemento selezionato dalla lista bloccati.
        Aggiorna sia la UI che lo storage persistente.
        Usa get_blocked_items() per sincronizzazione corretta.
        """
        selection = self.listbox.curselection()
        if not selection:
            self.show_feedback("Seleziona un elemento da rimuovere")
            return

        index = selection[0]
        items = get_blocked_items()

        if index >= len(items):
            self.show_feedback("Errore: elemento non trovato")
            self.refresh_list()
            return

        item_name = items[index]['name']

        if remove_blocked_item(index):
            self.listbox.delete(index)
            self.show_feedback(f"{item_name} rimosso!")
        else:
            self.show_feedback("Errore durante la rimozione")

    def refresh_list(self):
        """
        Aggiorna la listbox con tutti gli elementi salvati.
        Sincronizza l'interfaccia con lo storage persistente.
        Usa get_blocked_items() per dati sempre aggiornati.
        """
        self.listbox.delete(0, ttk.END)

        items = get_blocked_items()

        for item in items:
            self.listbox.insert(ttk.END, f"{item['name']}")

        self.show_feedback(f"Elementi bloccati: {len(items)}")

    # ========================================================================
    # FEEDBACK E GESTIONE FINESTRA
    # ========================================================================

    def show_feedback(self, message, duration=3000):
        """
        Mostra un messaggio di feedback temporaneo nella GUI.
        Il messaggio scompare automaticamente dopo la durata specificata.

        Args:
            message: Testo del messaggio
            duration: Durata in millisecondi (default 3000ms)
        """
        self.feedback_label.config(text=message)
        self.after(duration, lambda: self.feedback_label.config(text=""))

    def hide_window(self):
        """
        Nasconde la finestra principale (minimizza a tray).
        L'applicazione continua a funzionare in background.
        """
        self.withdraw()
        print("[INFO] Finestra nascosta")

    def quit_app(self):
        """
        Chiude completamente l'applicazione con conferma.
        Salva la configurazione prima di uscire.
        """
        if messagebox.askokcancel("Esci", "Vuoi uscire da Focus Mode App?"):
            print("[INFO] Chiusura applicazione richiesta")
            self.quit()
