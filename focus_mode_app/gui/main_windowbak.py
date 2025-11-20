"""
gui/main_window.py
Focus Mode App - Material You 3 Beautiful UI
Ispirato a Home Assistant dashboard
"""

from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from focus_mode_app.config import APP_TITLE
from focus_mode_app.core.blocker import (
    is_blocking_active,
    toggle_blocking,
    set_restore_enabled,
    is_restore_enabled,
    can_disable_blocking
)
from focus_mode_app.core.storage import (
    add_blocked_item,
    remove_blocked_item,
    get_blocked_items
)
from focus_mode_app.utils.tray_icon import update_tray_menu


class AppGui(ttk.Window):
    """Focus Mode App - Beautiful Material You 3 UI"""

    def __init__(self):
        super().__init__(themename="darkly")

        self.title(APP_TITLE)
        self.geometry("920x850")
        self._center_window()

        # Apply beautiful styling
        self._apply_beautiful_style()

        self._create_widgets()
        self.refresh_list()

        self.after(100, self.update_toggle_button)
        self.protocol("WM_DELETE_WINDOW", self.hide_window)

    def _center_window(self):
        """Centra finestra"""
        self.update_idletasks()
        width = 920
        height = 850
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _apply_beautiful_style(self):
        """Applica stile Material You 3 pulito"""
        # Background scuro come Home Assistant
        self.configure(bg='#111318')

        style = ttk.Style()

        # Card style (come Home Assistant)
        style.configure('Card.TLabelframe',
                        background='#1c1f26',
                        borderwidth=0,
                        relief='flat')

        style.configure('Card.TLabelframe.Label',
                        font=('Segoe UI', 13, 'bold'),
                        background='#1c1f26',
                        foreground='#ffffff',
                        padding=(0, 0, 0, 8))

        # Frame backgrounds
        style.configure('TFrame', background='#111318')

        # Labels
        style.configure('Title.TLabel',
                        font=('Segoe UI', 32, 'bold'),
                        background='#111318',
                        foreground='#ffffff')

        style.configure('Subtitle.TLabel',
                        font=('Segoe UI', 12),
                        background='#111318',
                        foreground='#8b8d98')

        style.configure('CardBody.TLabel',
                        font=('Segoe UI', 10),
                        background='#1c1f26',
                        foreground='#b3b5bd')

    def _create_widgets(self):
        """Crea UI bella e pulita"""
        # Scrollable main container
        main_canvas = ttk.Canvas(self, bg='#111318', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=VERTICAL, command=main_canvas.yview)

        scrollable = ttk.Frame(main_canvas)
        scrollable.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        window_id = main_canvas.create_window((0, 0), window=scrollable, anchor="nw", width=904)

        def configure_canvas(event):
            main_canvas.itemconfig(window_id, width=event.width - 16)

        main_canvas.bind('<Configure>', configure_canvas)
        main_canvas.configure(yscrollcommand=scrollbar.set)

        # Mouse wheel
        main_canvas.bind_all("<MouseWheel>", lambda e: main_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        main_canvas.bind_all("<Button-4>", lambda e: main_canvas.yview_scroll(-1, "units"))
        main_canvas.bind_all("<Button-5>", lambda e: main_canvas.yview_scroll(1, "units"))

        main_canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Content container
        content = ttk.Frame(scrollable)
        content.pack(fill=BOTH, expand=YES, padx=32, pady=32)

        # Header
        self._create_beautiful_header(content)

        # Hero button
        self._create_hero_button(content)

        # Cards grid
        self._create_focus_lock_card(content)
        self._create_restore_card(content)
        self._create_blocked_card(content)

    def _create_beautiful_header(self, parent):
        """Header stile Home Assistant"""
        header = ttk.Frame(parent)
        header.pack(fill=X, pady=(0, 28))

        # Icon + Title
        title_frame = ttk.Frame(header)
        title_frame.pack(anchor=W)

        ttk.Label(
            title_frame,
            text="🎯 Focus Mode",
            style='Title.TLabel'
        ).pack(side=LEFT)

        # Subtitle
        ttk.Label(
            header,
            text="Blocca le distrazioni e mantieni la concentrazione",
            style='Subtitle.TLabel'
        ).pack(anchor=W, pady=(6, 0))

    def _create_hero_button(self, parent):
        """Grande bottone FAB centrale"""
        btn_container = ttk.Frame(parent)
        btn_container.pack(fill=X, pady=(0, 24))

        self.toggle_btn = ttk.Button(
            btn_container,
            text="🔓 ATTIVA FOCUS MODE",
            command=self.toggle_blocking,
            bootstyle="success",
            width=60
        )
        self.toggle_btn.pack(fill=X, ipady=18)

    def _create_focus_lock_card(self, parent):
        """Card Focus Lock pulita"""
        card = ttk.LabelFrame(
            parent,
            text="⏱️  Focus Lock",
            style='Card.TLabelframe',
            padding=20
        )
        card.pack(fill=X, pady=(0, 20))

        # Mode selector chips
        mode_frame = ttk.Frame(card)
        mode_frame.pack(fill=X, pady=(0, 16))

        self.lock_mode = ttk.StringVar(value="timer")

        chip_container = ttk.Frame(mode_frame)
        chip_container.pack()

        ttk.Radiobutton(
            chip_container,
            text="⏲️ Timer",
            variable=self.lock_mode,
            value="timer",
            bootstyle="primary-toolbutton",
            command=self.update_lock_visibility
        ).pack(side=LEFT, padx=(0, 12))

        ttk.Radiobutton(
            chip_container,
            text="🕐 Target Time",
            variable=self.lock_mode,
            value="target",
            bootstyle="primary-toolbutton",
            command=self.update_lock_visibility
        ).pack(side=LEFT)

        # Timer input (inline e pulito)
        self.timer_frame = ttk.Frame(card)
        self.timer_frame.pack(fill=X, pady=(0, 16))

        timer_row = ttk.Frame(self.timer_frame)
        timer_row.pack()

        ttk.Label(
            timer_row,
            text="Durata:",
            style='CardBody.TLabel'
        ).pack(side=LEFT, padx=(0, 12))

        self.timer_entry = ttk.Entry(timer_row, width=8, font=('Segoe UI', 11))
        self.timer_entry.insert(0, "25")
        self.timer_entry.pack(side=LEFT, padx=(0, 8))

        ttk.Label(
            timer_row,
            text="minuti",
            style='CardBody.TLabel'
        ).pack(side=LEFT)

        # Target input
        self.target_frame = ttk.Frame(card)

        target_row = ttk.Frame(self.target_frame)
        target_row.pack()

        ttk.Label(
            target_row,
            text="Fino alle:",
            style='CardBody.TLabel'
        ).pack(side=LEFT, padx=(0, 12))

        self.hour_entry = ttk.Entry(target_row, width=4, font=('Segoe UI', 11))
        self.hour_entry.insert(0, "14")
        self.hour_entry.pack(side=LEFT, padx=(0, 6))

        ttk.Label(
            target_row,
            text=":",
            font=('Segoe UI', 14, 'bold')
        ).pack(side=LEFT, padx=4)

        self.minute_entry = ttk.Entry(target_row, width=4, font=('Segoe UI', 11))
        self.minute_entry.insert(0, "30")
        self.minute_entry.pack(side=LEFT, padx=(6, 0))

        # Activate button
        ttk.Button(
            card,
            text="🔒 Attiva Lock",
            command=self.activate_lock,
            bootstyle="primary",
            width=25
        ).pack(fill=X, pady=(0, 16), ipady=12)

        # Status badge
        status_frame = ttk.Frame(card)
        status_frame.pack()

        self.status_label = ttk.Label(
            status_frame,
            text="● Nessun lock attivo",
            font=('Segoe UI', 10),
            foreground='#6c757d',
            background='#1c1f26'
        )
        self.status_label.pack()

        self.update_lock_visibility()
        self.update_timer_display()

    def _create_restore_card(self, parent):
        """Card Auto-Restore pulita"""
        card = ttk.LabelFrame(
            parent,
            text="♻️  Auto-Restore",
            style='Card.TLabelframe',
            padding=20
        )
        card.pack(fill=X, pady=(0, 20))

        # Description
        ttk.Label(
            card,
            text="Ripristina automaticamente le app quando disattivi il focus mode",
            style='CardBody.TLabel',
            wraplength=800
        ).pack(anchor=W, pady=(0, 16))

        # List con stile pulito
        list_container = ttk.Frame(card)
        list_container.pack(fill=X, pady=(0, 16))

        list_scroll = ttk.Scrollbar(list_container)
        list_scroll.pack(side=RIGHT, fill=Y)

        self.restore_listbox = ttk.Treeview(
            list_container,
            show='tree',
            height=3,
            selectmode='browse',
            yscrollcommand=list_scroll.set
        )
        self.restore_listbox.pack(side=LEFT, fill=BOTH, expand=YES)
        list_scroll.config(command=self.restore_listbox.yview)

        # Buttons inline
        btn_row = ttk.Frame(card)
        btn_row.pack(fill=X, pady=(0, 16))

        ttk.Button(
            btn_row,
            text="+ Aggiungi",
            command=self.add_to_restore,
            bootstyle="info-outline",
            width=18
        ).pack(side=LEFT, expand=YES, fill=X, padx=(0, 12), ipady=10)

        ttk.Button(
            btn_row,
            text="Rimuovi",
            command=self.remove_from_restore,
            bootstyle="secondary-outline",
            width=18
        ).pack(side=LEFT, expand=YES, fill=X, ipady=10)

        # Toggle switch style
        self.restore_btn = ttk.Button(
            card,
            text="🟢 Auto-Restore ATTIVO",
            command=self.toggle_restore,
            bootstyle="success-outline"
        )
        self.restore_btn.pack(fill=X, ipady=10)

        self.refresh_restore_list()

    def _create_blocked_card(self, parent):
        """Card Elementi Bloccati pulita"""
        card = ttk.LabelFrame(
            parent,
            text="🚫 Elementi Bloccati",
            style='Card.TLabelframe',
            padding=20
        )
        card.pack(fill=BOTH, expand=YES)

        # Type selector chips
        type_frame = ttk.Frame(card)
        type_frame.pack(fill=X, pady=(0, 16))

        self.item_type = ttk.StringVar(value="app")

        chip_container = ttk.Frame(type_frame)
        chip_container.pack()

        ttk.Radiobutton(
            chip_container,
            text="📱 App",
            variable=self.item_type,
            value="app",
            bootstyle="primary-toolbutton",
            command=self.update_desc
        ).pack(side=LEFT, padx=(0, 12))

        ttk.Radiobutton(
            chip_container,
            text="🌐 WebApp",
            variable=self.item_type,
            value="webapp",
            bootstyle="primary-toolbutton",
            command=self.update_desc
        ).pack(side=LEFT)

        # Description
        self.desc_label = ttk.Label(
            card,
            text="",
            style='CardBody.TLabel',
            wraplength=800
        )
        self.desc_label.pack(anchor=W, pady=(0, 12))
        self.update_desc()

        # Input + Add button inline
        input_row = ttk.Frame(card)
        input_row.pack(fill=X, pady=(0, 16))

        self.entry = ttk.Entry(input_row, font=('Segoe UI', 11))
        self.entry.pack(side=LEFT, expand=YES, fill=X, padx=(0, 12))

        ttk.Button(
            input_row,
            text="+ Aggiungi",
            command=self.add_item,
            bootstyle="primary",
            width=14
        ).pack(side=LEFT, ipady=10)

        # List pulita
        list_container = ttk.Frame(card)
        list_container.pack(fill=BOTH, expand=YES, pady=(0, 16))

        list_scroll = ttk.Scrollbar(list_container)
        list_scroll.pack(side=RIGHT, fill=Y)

        self.listbox = ttk.Treeview(
            list_container,
            show='tree',
            height=8,
            selectmode='browse',
            yscrollcommand=list_scroll.set
        )
        self.listbox.pack(side=LEFT, fill=BOTH, expand=YES)
        list_scroll.config(command=self.listbox.yview)

        # Remove button
        ttk.Button(
            card,
            text="Rimuovi Selezionato",
            command=self.remove_item,
            bootstyle="danger-outline"
        ).pack(fill=X, ipady=10)

    # ========================================================================
    # LOGIC METHODS (mantieni quelli esistenti)
    # ========================================================================

    def update_lock_visibility(self):
        if self.lock_mode.get() == "timer":
            self.timer_frame.pack(fill=X, pady=(0, 16))
            self.target_frame.pack_forget()
        else:
            self.timer_frame.pack_forget()
            self.target_frame.pack(fill=X, pady=(0, 16))

    def activate_lock(self):
        try:
            from focus_mode_app.core.focus_lock import focus_lock
            mode = self.lock_mode.get()

            if mode == "timer":
                minutes = int(self.timer_entry.get())
                if minutes > 0 and focus_lock.set_timer_lock(minutes):
                    messagebox.showinfo("Success", f"Timer Lock: {minutes} min")
                    if not is_blocking_active():
                        toggle_blocking()
                        self.update_toggle_button()
            else:
                hour = int(self.hour_entry.get())
                minute = int(self.minute_entry.get())
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    if focus_lock.set_target_time_lock(hour, minute):
                        messagebox.showinfo("Success", f"Target: {hour:02d}:{minute:02d}")
                        if not is_blocking_active():
                            toggle_blocking()
                            self.update_toggle_button()
        except Exception as e:
            messagebox.showerror("Errore", str(e))

    def update_timer_display(self):
        try:
            from focus_mode_app.core.focus_lock import focus_lock
            if focus_lock.is_locked():
                info = focus_lock.get_lock_info()
                self.status_label.config(
                    text=f"🔒 LOCKED - {info['remaining_time']}",
                    foreground='#dc3545'
                )
                self.toggle_btn.config(state="disabled")
            else:
                self.status_label.config(
                    text="● Nessun lock attivo",
                    foreground='#6c757d'
                )
                self.toggle_btn.config(state="normal")
        except:
            pass
        self.after(1000, self.update_timer_display)

    def toggle_blocking(self):
        if is_blocking_active():
            can_disable, reason = can_disable_blocking()
            if not can_disable:
                messagebox.showwarning("Blocco Attivo", reason)
                return
        toggle_blocking()
        self.update_toggle_button()
        update_tray_menu()

    def update_toggle_button(self):
        if is_blocking_active():
            self.toggle_btn.config(text="🔒 DISATTIVA FOCUS MODE", bootstyle="danger")
        else:
            self.toggle_btn.config(text="🔓 ATTIVA FOCUS MODE", bootstyle="success")

    def update_desc(self):
        if self.item_type.get() == "app":
            self.desc_label.config(text="Nome eseguibile (es: firefox, telegram)")
        else:
            self.desc_label.config(text="URL o dominio (es: web.whatsapp.com)")

    def add_item(self):
        name = self.entry.get().strip()
        item_type = self.item_type.get()
        if item_type == "app":
            name = name.lower()
        if name and add_blocked_item(name, item_type):
            self.refresh_list()
            self.entry.delete(0, END)
            messagebox.showinfo("Success", f"{name} aggiunto!")

    def remove_item(self):
        selection = self.listbox.selection()
        if not selection:
            return
        item = self.listbox.item(selection[0])
        try:
            index = int(item['text'].split('.')[0]) - 1
            items = get_blocked_items()
            if index < len(items) and remove_blocked_item(index):
                self.refresh_list()
                messagebox.showinfo("Success", f"{items[index]['name']} rimosso!")
        except:
            pass

    def refresh_list(self):
        self.listbox.delete(*self.listbox.get_children())
        items = get_blocked_items()
        for idx, item in enumerate(items, 1):
            icon = "📱" if item['type'] == "app" else "🌐"
            self.listbox.insert('', 'end', text=f"{idx}. {icon} {item['name']}")

    def add_to_restore(self):
        selection = self.listbox.selection()
        if not selection:
            return
        try:
            item = self.listbox.item(selection[0])
            index = int(item['text'].split('.')[0]) - 1
            items = get_blocked_items()
            if index < len(items):
                from focus_mode_app.core.session import session_tracker
                session_tracker.add_to_restore(items[index]["name"])
                self.refresh_restore_list()
                messagebox.showinfo("Success", "Aggiunto al restore")
        except Exception as e:
            messagebox.showerror("Errore", str(e))

    def remove_from_restore(self):
        selection = self.restore_listbox.selection()
        if not selection:
            return
        try:
            from focus_mode_app.core.session import session_tracker
            item = self.restore_listbox.item(selection[0])
            app_name = item['text'].replace("♻️ ", "")
            session_tracker.remove_from_restore(app_name)
            self.refresh_restore_list()
            messagebox.showinfo("Success", "Rimosso")
        except Exception as e:
            messagebox.showerror("Errore", str(e))

    def refresh_restore_list(self):
        self.restore_listbox.delete(*self.restore_listbox.get_children())
        try:
            from focus_mode_app.core.session import session_tracker
            for app_name in session_tracker.restore_list.keys():
                self.restore_listbox.insert('', 'end', text=f"♻️ {app_name}")
        except:
            pass

    def toggle_restore(self):
        new_state = not is_restore_enabled()
        set_restore_enabled(new_state)
        if new_state:
            self.restore_btn.config(text="🟢 Auto-Restore ATTIVO", bootstyle="success-outline")
        else:
            self.restore_btn.config(text="🔴 Auto-Restore DISATTIVO", bootstyle="danger-outline")

    def hide_window(self):
        self.withdraw()

    def quit_app(self):
        if messagebox.askokcancel("Esci", "Vuoi uscire?"):
            self.quit()
