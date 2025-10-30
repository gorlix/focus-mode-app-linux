"""
gui/main_window.py
Finestra principale dell'applicazione Modalità Studio.
"""

from tkinter import messagebox
import ttkbootstrap as ttk

from config import WINDOW_WIDTH, WINDOW_HEIGHT, GUI_THEME, APP_TITLE
from core.blocker import is_blocking_active, toggle_blocking
from core.storage import (
    blocked_items,
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
    Finestra principale dell'applicazione Modalità Studio.
    Gestisce l'interfaccia utente per configurare app e webapp da bloccare.
    """
    
    def __init__(self):
        """Inizializza la finestra principale."""
        super().__init__(themename=GUI_THEME)
        
        self.title(APP_TITLE)
        
        # Centra finestra e imposta dimensioni
        set_window_center(self, WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Applica stile Material 3
        apply_material3_style(self)
        
        # Crea interfaccia
        self._create_widgets()
        
        # Carica liste salvate (forza il caricamento da file)
        from core.storage import load_blocked_items
        load_blocked_items()
        self.refresh_list()
        
        # Gestione chiusura finestra (X) - nasconde invece di chiudere
        self.protocol("WM_DELETE_WINDOW", self.hide_window)
    
    # ========================================================================
    # CREAZIONE INTERFACCIA
    # ========================================================================
    
    def _create_widgets(self):
        """Crea tutti i widget dell'interfaccia."""
        # Frame principale con padding
        main_frame = create_card_frame(self, padx=24, pady=24)
        
        # Titolo
        self._create_title(main_frame)
        
        # Bottone toggle modalità
        self._create_toggle_button(main_frame)
        
        # Sezione elementi bloccati
        self._create_blocked_section(main_frame)
        
        # Label feedback
        self._create_feedback_label(main_frame)
        
        # Bottoni azioni
        self._create_action_buttons(main_frame)
    
    def _create_title(self, parent):
        """Crea il titolo principale."""
        title = material_label(parent, "🎯 Modalità Studio", style_type="title")
        title.pack(pady=(0, 10))
    
    def _create_toggle_button(self, parent):
        """Crea il bottone toggle per attivare/disattivare blocco."""
        self.toggle_btn = ttk.Button(
            parent,
            text="▶️ ATTIVA MODALITÀ STUDIO",
            command=self.toggle_blocking,
            bootstyle="success-outline",
            width=30
        )
        self.toggle_btn.pack(pady=(0, 20))
    
    def _create_blocked_section(self, parent):
        """Crea la sezione per gestire elementi bloccati."""
        section = ttk.LabelFrame(
            parent, 
            text="🚫 Elementi Bloccati", 
            bootstyle="primary",
            padding=16
        )
        section.pack(fill="both", expand=True, pady=(0, 16))
        
        # Radio buttons per tipo
        self._create_type_selector(section)
        
        # Label descrittiva
        self.desc_label = material_label(section, "")
        self.desc_label.pack(anchor="w", pady=(0, 8))
        self.update_description()
        
        # Entry per nome/URL
        self.entry = material_entry(section)
        self.entry.pack(fill="x", pady=(0, 8))
        
        # Bottoni add/remove
        self._create_item_buttons(section)
        
        # Listbox
        self.listbox = material_listbox(section, height=6)
        self.listbox.pack(fill="both", expand=True)
    
    def _create_type_selector(self, parent):
        """Crea i radio button per selezionare tipo app/webapp."""
        radio_frame = ttk.Frame(parent)
        radio_frame.pack(fill="x", pady=(0, 12))
        
        self.item_type = ttk.StringVar(value="app")
        
        radio_app = ttk.Radiobutton(
            radio_frame,
            text="📱 App Nativa",
            variable=self.item_type,
            value="app",
            bootstyle="primary"
        )
        radio_app.pack(side="left", padx=(0, 16))
        
        radio_webapp = ttk.Radiobutton(
            radio_frame,
            text="🌐 Webapp",
            variable=self.item_type,
            value="webapp",
            bootstyle="info"
        )
        radio_webapp.pack(side="left")
        
        # Aggiorna descrizione quando cambia selezione
        self.item_type.trace_add("write", lambda *args: self.update_description())
    
    def _create_item_buttons(self, parent):
        """Crea i bottoni per aggiungere/rimuovere elementi."""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", pady=(0, 8))
        
        btn_add = material_button(
            btn_frame, 
            "➕ Aggiungi", 
            self.add_item,
            button_type="primary"
        )
        btn_add.pack(side="left", expand=True, fill="x", padx=(0, 4))
        
        btn_remove = ttk.Button(
            btn_frame, 
            text="🗑️ Rimuovi", 
            command=self.remove_item,
            bootstyle="danger"
        )
        btn_remove.pack(side="right", expand=True, fill="x", padx=(4, 0))
    
    def _create_feedback_label(self, parent):
        """Crea il label per feedback temporaneo."""
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
            "🔄 Aggiorna", 
            self.refresh_list,
            button_type="secondary"
        )
        btn_refresh.pack(side="left", expand=True, fill="x", padx=(0, 4))
        
        btn_quit = ttk.Button(
            actions_frame, 
            text="🚪 Esci", 
            command=self.quit_app,
            bootstyle="danger"
        )
        btn_quit.pack(side="right", expand=True, fill="x", padx=(4, 0))
    
    # ========================================================================
    # GESTIONE BLOCCO
    # ========================================================================
    
    def toggle_blocking(self):
        """Toggle dello stato blocco (attivo/disattivo)."""
        new_state = toggle_blocking()
        self.update_toggle_button()
        
        # Aggiorna anche il menu tray
        update_tray_menu()
    
    def update_toggle_button(self):
        """Aggiorna il bottone toggle in base allo stato corrente."""
        if is_blocking_active():
            self.toggle_btn.config(
                text="⏸️ DISATTIVA MODALITÀ STUDIO",
                bootstyle="danger"
            )
            self.show_feedback("🔒 Modalità Studio ATTIVATA - Le app verranno bloccate")
        else:
            self.toggle_btn.config(
                text="▶️ ATTIVA MODALITÀ STUDIO",
                bootstyle="success-outline"
            )
            self.show_feedback("🔓 Modalità Studio DISATTIVATA - Nessun blocco attivo")
    
    # ========================================================================
    # GESTIONE ELEMENTI
    # ========================================================================
    
    def update_description(self):
        """Aggiorna il testo descrittivo in base al tipo selezionato."""
        if self.item_type.get() == "app":
            self.desc_label.config(text="Nome eseguibile (es: firefox, telegram):")
        else:
            self.desc_label.config(text="URL o stringa comando (es: web.whatsapp.com):")
    
    def add_item(self):
        """Aggiunge un elemento alla lista bloccati."""
        name = self.entry.get().strip()
        item_type = self.item_type.get()
        
        # Normalizza il nome (lowercase solo per app)
        if item_type == "app":
            name = name.lower()
        
        if not name:
            self.show_feedback("⚠️ Inserisci un valore valido")
            return
        
        # Usa la funzione di storage
        if add_blocked_item(name, item_type):
            # Aggiungi alla listbox
            emoji = "📱" if item_type == "app" else "🌐"
            self.listbox.insert(ttk.END, f"{emoji} {name}")
            
            self.show_feedback(f"✅ '{name}' aggiunto e salvato!")
            self.entry.delete(0, ttk.END)
        else:
            self.show_feedback("⚠️ Elemento già presente o non valido")
    
    def remove_item(self):
        """Rimuove l'elemento selezionato dalla lista."""
        selection = self.listbox.curselection()
        if not selection:
            self.show_feedback("⚠️ Seleziona un elemento da rimuovere")
            return
        
        index = selection[0]
        
        # Ricarica la lista per sicurezza prima di rimuovere
        from core.storage import blocked_items
        
        # Verifica che l'indice sia valido
        if index >= len(blocked_items):
            self.show_feedback("⚠️ Errore: elemento non trovato")
            print(f"[ERROR] Indice {index} fuori range (lista ha {len(blocked_items)} elementi)")
            print(f"[DEBUG] Listbox ha {self.listbox.size()} elementi")
            # Forza refresh per risincronizzare
            self.refresh_list()
            return
        
        # Salva il nome prima di rimuoverlo
        item_name = blocked_items[index]['name']
        
        # Usa la funzione di storage (che rimuove e salva)
        if remove_blocked_item(index):
            # Rimuovi dalla listbox
            self.listbox.delete(index)
            self.show_feedback(f"🗑️ '{item_name}' rimosso!")
        else:
            self.show_feedback("⚠️ Errore durante la rimozione")
 
    def refresh_list(self):
        """Aggiorna la listbox con tutti gli elementi salvati."""
        from core.storage import blocked_items
        
        self.listbox.delete(0, ttk.END)
        
        for item in get_blocked_items():
            emoji = "📱" if item["type"] == "app" else "🌐"
            self.listbox.insert(ttk.END, f"{emoji} {item['name']}")
        
        print(f"[DEBUG] Refresh completato: {len(blocked_items)} elementi in lista globale, {self.listbox.size()} nella listbox")
        self.show_feedback(f"📋 Elementi bloccati: {len(blocked_items)}")
    
    # ========================================================================
    # FEEDBACK E UI
    # ========================================================================
    
    def show_feedback(self, message, duration=3000):
        """
        Mostra un messaggio di feedback temporaneo.
        
        Args:
            message: Messaggio da mostrare
            duration: Durata in millisecondi (default 3000)
        """
        self.feedback_label.config(text=message)
        self.after(duration, lambda: self.feedback_label.config(text=""))
    
    # ========================================================================
    # FINESTRA
    # ========================================================================
    
    def hide_window(self):
        """Nasconde la finestra (minimizza a tray)."""
        self.withdraw()
        print("[INFO] Finestra nascosta")
    
    def quit_app(self):
        """Chiude completamente l'applicazione."""
        if messagebox.askokcancel("🚪 Esci", "Vuoi uscire dalla modalità studio?"):
            print("[INFO] Chiusura applicazione richiesta dalla GUI")
            # Il salvataggio sarà gestito dal tray icon callback
            self.quit()

