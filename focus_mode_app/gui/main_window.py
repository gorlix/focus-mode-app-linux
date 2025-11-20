"""
gui/main_window.py
Focus Mode App - KivyMD Material You 3 UI
Compatible with KivyMD 1.x - Fixed Layout
"""

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import OneLineAvatarIconListItem, IconLeftWidget, IRightBodyTouch, MDList
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton, MDFillRoundFlatButton, MDFillRoundFlatIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDSwitch, MDCheckbox
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.utils import get_color_from_hex

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
from focus_mode_app.gui.material_theme import MaterialYouColors


class FocusModeScreen(MDScreen):
    """Main screen for Focus Mode App"""
    pass


class RightContainer(IRightBodyTouch, MDBoxLayout):
    """Custom right container for list items"""
    adaptive_width = True


class FocusModeApp(MDApp):
    """Focus Mode App - KivyMD Material You 3"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = APP_TITLE

        # State
        self.lock_mode = "timer"
        self.item_type = "app"
        self.selected_blocked_index = None
        
        # Dialog reference
        self.current_dialog = None

        # Widget references
        self.timer_input_layout = None
        self.target_input_layout = None
        self.colors = MaterialYouColors.DEFAULT_COLORS

    def build(self):
        """Build the app UI programmatically"""
        # Set window size
        Window.size = (980, 900)
        
        # Configure theme
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.material_style = "M3"
        
        # Load Material You colors
        self._load_material_you_colors()
        
        # Set background color
        Window.clearcolor = get_color_from_hex(self.colors["background"])

        # Create main screen
        screen = FocusModeScreen()
        screen.md_bg_color = get_color_from_hex(self.colors["background"])

        # Create scrollable content
        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True, bar_width=dp(8))
        
        # Main container
        main_layout = MDGridLayout(
            cols=1,
            size_hint_y=None,
            padding=[dp(24), dp(24)],
            spacing=dp(24),
            md_bg_color=get_color_from_hex(self.colors["background"])
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))

        # Add all sections
        main_layout.add_widget(self._create_header())
        main_layout.add_widget(self._create_toggle_button())
        
        # Cards container
        cards_layout = MDGridLayout(
            cols=1,
            spacing=dp(24),
            size_hint_y=None
        )
        cards_layout.bind(minimum_height=cards_layout.setter('height'))
        
        cards_layout.add_widget(self._create_focus_lock_card())
        # Merged Blocked & Restore Card
        cards_layout.add_widget(self._create_blocked_card())
        
        main_layout.add_widget(cards_layout)

        scroll.add_widget(main_layout)
        screen.add_widget(scroll)

        # Schedule updates
        Clock.schedule_once(lambda dt: self.update_toggle_button(), 0.5)
        Clock.schedule_once(lambda dt: self.refresh_blocked_list(), 0.5)
        Clock.schedule_interval(self._update_timer_display, 1)

        return screen

    def _load_material_you_colors(self):
        """Load Material You colors"""
        try:
            plasma_colors = MaterialYouColors.get_plasma_colors()
            if plasma_colors:
                self.colors = plasma_colors
        except:
            pass

    def _create_header(self):
        """Create header"""
        layout = MDBoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8), padding=[0, 0, 0, dp(16)])
        layout.bind(minimum_height=layout.setter('height'))

        title_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(64), spacing=dp(16))
        
        icon_label = MDIcon(
            icon="target",
            theme_text_color="Custom",
            text_color=get_color_from_hex(self.colors["primary"]),
            size_hint=(None, None),
            size=(dp(64), dp(64)),
            halign="center",
            font_size="48sp"
        )
        
        title = MDLabel(
            text="Focus Mode",
            font_style="H3",
            theme_text_color="Custom",
            text_color=get_color_from_hex(self.colors["on_background"]),
            size_hint_y=None,
            height=dp(64),
            valign="center"
        )
        
        title_box.add_widget(icon_label)
        title_box.add_widget(title)

        subtitle = MDLabel(
            text="Blocca le distrazioni e mantieni la concentrazione",
            font_style="Body1",
            theme_text_color="Custom",
            text_color=get_color_from_hex(self.colors["on_surface_variant"]),
            size_hint_y=None,
            height=dp(24)
        )

        layout.add_widget(title_box)
        layout.add_widget(subtitle)

        return layout

    def _create_toggle_button(self):
        """Create main toggle button"""
        self.toggle_btn = MDFillRoundFlatIconButton(
            text="ATTIVA FOCUS MODE",
            icon="lock-open",
            font_size="18sp",
            size_hint=(1, None),
            height=dp(64),
            on_release=lambda x: self.toggle_blocking()
        )
        return self.toggle_btn

    def _create_card_base(self, height=None):
        """Create a base card with Material 3 styling"""
        card = MDCard(
            orientation='vertical',
            padding=dp(24),
            spacing=dp(16),
            size_hint_y=None,
            radius=[dp(16)],
            elevation=1,
            md_bg_color=get_color_from_hex(self.colors["surface_container"])
        )
        if height:
            card.height = height
        else:
            card.bind(minimum_height=card.setter('height'))
        return card

    def _create_section_title(self, text, icon=""):
        """Create a section title"""
        box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(32), spacing=dp(12))
        if icon:
            lbl_icon = MDIcon(
                icon=icon, 
                size_hint=(None, None), 
                size=(dp(24), dp(32)), 
                theme_text_color="Custom",
                text_color=get_color_from_hex(self.colors["primary"]),
                font_size="24sp"
            )
            box.add_widget(lbl_icon)
            
        lbl = MDLabel(
            text=text,
            font_style="H6",
            theme_text_color="Custom",
            text_color=get_color_from_hex(self.colors["on_surface"])
        )
        box.add_widget(lbl)
        return box

    def _create_focus_lock_card(self):
        """Create focus lock card"""
        card = self._create_card_base()

        # Title
        card.add_widget(self._create_section_title("Focus Lock Timer", "timer"))

        # Description
        desc = MDLabel(
            text="Blocca temporaneamente il focus mode per evitare distrazioni impulsive.",
            font_style="Body2",
            theme_text_color="Custom",
            text_color=get_color_from_hex(self.colors["on_surface_variant"]),
            size_hint_y=None,
            height=dp(40)
        )
        card.add_widget(desc)

        # Mode buttons
        mode_layout = MDBoxLayout(size_hint=(1, None), height=dp(48), spacing=dp(12))

        timer_btn = MDFillRoundFlatIconButton(
            text="Timer",
            icon="timer",
            on_release=lambda x: self.set_lock_mode("timer"),
            md_bg_color=get_color_from_hex(self.colors["primary_container"]),
            text_color=get_color_from_hex(self.colors["on_primary_container"]),
        )
        target_btn = MDFillRoundFlatIconButton(
            text="Target",
            icon="clock-time-four",
            on_release=lambda x: self.set_lock_mode("target"),
            md_bg_color=get_color_from_hex(self.colors["surface_container_highest"]),
            text_color=get_color_from_hex(self.colors["on_surface_variant"]),
        )
        
        self.mode_timer_btn = timer_btn
        self.mode_target_btn = target_btn

        mode_layout.add_widget(timer_btn)
        mode_layout.add_widget(target_btn)
        card.add_widget(mode_layout)

        # Timer input
        self.timer_input_layout = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(80),
            spacing=dp(8)
        )

        timer_label = MDLabel(
            text="Durata (minuti)",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=get_color_from_hex(self.colors["on_surface_variant"]),
            size_hint_y=None,
            height=dp(20)
        )

        self.timer_entry = MDTextField(
            hint_text="25",
            text="25",
            mode="fill",
            fill_color_normal=get_color_from_hex(self.colors["surface_container_highest"]),
            line_color_focus=get_color_from_hex(self.colors["primary"]),
            size_hint=(None, None),
            size=(dp(150), dp(50))
        )

        self.timer_input_layout.add_widget(timer_label)
        self.timer_input_layout.add_widget(self.timer_entry)
        card.add_widget(self.timer_input_layout)

        # Target input (hidden initially)
        self.target_input_layout = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=0,
            spacing=dp(8),
            opacity=0
        )

        target_label = MDLabel(
            text="Orario di sblocco (HH:MM)",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=get_color_from_hex(self.colors["on_surface_variant"]),
            size_hint_y=None,
            height=dp(20)
        )

        target_row = MDBoxLayout(size_hint=(None, None), size=(dp(200), dp(50)), spacing=dp(12))

        self.hour_entry = MDTextField(
            hint_text="14", text="14", 
            mode="fill",
            fill_color_normal=get_color_from_hex(self.colors["surface_container_highest"]),
            size_hint=(None, None), size=(dp(80), dp(50))
        )
        colon = MDLabel(text=":", font_style="H5", size_hint=(None, None), size=(dp(20), dp(50)), halign="center")
        self.minute_entry = MDTextField(
            hint_text="30", text="30", 
            mode="fill",
            fill_color_normal=get_color_from_hex(self.colors["surface_container_highest"]),
            size_hint=(None, None), size=(dp(80), dp(50))
        )

        target_row.add_widget(self.hour_entry)
        target_row.add_widget(colon)
        target_row.add_widget(self.minute_entry)

        self.target_input_layout.add_widget(target_label)
        self.target_input_layout.add_widget(target_row)
        card.add_widget(self.target_input_layout)

        # Activate button
        activate_btn = MDFillRoundFlatIconButton(
            text="Attiva Lock",
            icon="lock",
            size_hint=(1, None),
            height=dp(48),
            on_release=lambda x: self.activate_lock()
        )
        card.add_widget(activate_btn)

        # Status label
        self.status_label = MDLabel(
            text="Nessun lock attivo",
            font_style="Body2",
            theme_text_color="Custom",
            text_color=get_color_from_hex(self.colors["outline"]),
            halign="center",
            size_hint_y=None,
            height=dp(30)
        )
        card.add_widget(self.status_label)

        return card

    def _create_blocked_card(self):
        """Create blocked items card with integrated restore controls"""
        card = self._create_card_base()

        # Title
        card.add_widget(self._create_section_title("Gestione Blocchi & Restore", "shield-check"))

        # Type buttons
        type_layout = MDBoxLayout(size_hint=(None, None), size=(dp(300), dp(48)), spacing=dp(12))

        app_btn = MDFillRoundFlatIconButton(
            text="App", 
            icon="cellphone",
            on_release=lambda x: self.set_item_type("app"),
            md_bg_color=get_color_from_hex(self.colors["primary_container"]),
            text_color=get_color_from_hex(self.colors["on_primary_container"]),
        )
        web_btn = MDFillRoundFlatIconButton(
            text="Web", 
            icon="web",
            on_release=lambda x: self.set_item_type("webapp"),
            md_bg_color=get_color_from_hex(self.colors["surface_container_highest"]),
            text_color=get_color_from_hex(self.colors["on_surface_variant"]),
        )
        
        self.type_app_btn = app_btn
        self.type_web_btn = web_btn

        type_layout.add_widget(app_btn)
        type_layout.add_widget(web_btn)
        card.add_widget(type_layout)

        # Description
        self.item_desc_label = MDLabel(
            text="Inserisci il nome dell'eseguibile (es: firefox, telegram)",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=get_color_from_hex(self.colors["on_surface_variant"]),
            size_hint_y=None,
            height=dp(24)
        )
        card.add_widget(self.item_desc_label)

        # Input row
        input_layout = MDBoxLayout(size_hint=(1, None), height=dp(56), spacing=dp(12))

        self.item_entry = MDTextField(
            hint_text="Nome elemento",
            mode="fill",
            fill_color_normal=get_color_from_hex(self.colors["surface_container_highest"]),
            size_hint=(1, None),
            height=dp(56)
        )
        add_btn = MDIconButton(
            icon="plus",
            theme_icon_color="Custom",
            icon_color=get_color_from_hex(self.colors["primary"]),
            on_release=lambda x: self.add_item()
        )

        input_layout.add_widget(self.item_entry)
        input_layout.add_widget(add_btn)
        card.add_widget(input_layout)

        # Table Header
        card.add_widget(self._create_blocked_list_header())

        # List
        scroll = ScrollView(size_hint=(1, None), height=dp(300))
        self.blocked_list_container = MDList(spacing=dp(8), padding=[0, dp(8)])
        scroll.add_widget(self.blocked_list_container)
        card.add_widget(scroll)

        # Global Restore Switch (moved from restore card)
        switch_layout = MDBoxLayout(size_hint=(1, None), height=dp(48), spacing=dp(12))

        switch_label = MDLabel(
            text="Abilita Auto-Restore Globale", 
            font_style="Body1", 
            theme_text_color="Custom",
            text_color=get_color_from_hex(self.colors["on_surface"]),
            size_hint_y=None,
            height=dp(48),
            valign="center"
        )

        self.restore_switch = MDSwitch()
        self.restore_switch.active = is_restore_enabled()
        self.restore_switch.bind(active=lambda x, v: self.toggle_restore(v))
        self.restore_switch.size_hint = (None, None)
        self.restore_switch.height = dp(48)

        switch_layout.add_widget(switch_label)
        switch_layout.add_widget(self.restore_switch)
        card.add_widget(switch_layout)

        return card

    def _create_blocked_list_header(self):
        """Create header for the blocked items list (Table style)"""
        header = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            padding=[dp(16), 0],
            spacing=dp(8),
            md_bg_color=get_color_from_hex(self.colors["surface_container_highest"]),
            radius=[dp(8)]
        )
        
        # Column 1: Name
        header.add_widget(MDLabel(
            text="Elemento",
            font_style="Subtitle2",
            theme_text_color="Custom",
            text_color=get_color_from_hex(self.colors["on_surface_variant"]),
            size_hint_x=0.5,
            valign="center"
        ))
        
        # Column 2: Auto-Restore
        header.add_widget(MDLabel(
            text="Auto-Restore",
            font_style="Subtitle2",
            theme_text_color="Custom",
            text_color=get_color_from_hex(self.colors["on_surface_variant"]),
            size_hint_x=0.3,
            halign="center",
            valign="center"
        ))
        
        # Column 3: Actions
        header.add_widget(MDLabel(
            text="Elimina",
            font_style="Subtitle2",
            theme_text_color="Custom",
            text_color=get_color_from_hex(self.colors["on_surface_variant"]),
            size_hint_x=0.2,
            halign="center",
            valign="center"
        ))
        
        return header

    # ========================================================================
    # LOGIC METHODS
    # ========================================================================

    def set_lock_mode(self, mode):
        """Set lock mode"""
        self.lock_mode = mode

        if mode == "timer":
            Animation(opacity=1, height=dp(80), duration=0.3).start(self.timer_input_layout)
            Animation(opacity=0, height=0, duration=0.3).start(self.target_input_layout)
            
            self.mode_timer_btn.md_bg_color = get_color_from_hex(self.colors["primary_container"])
            self.mode_timer_btn.text_color = get_color_from_hex(self.colors["on_primary_container"])
            self.mode_target_btn.md_bg_color = get_color_from_hex(self.colors["surface_container_highest"])
            self.mode_target_btn.text_color = get_color_from_hex(self.colors["on_surface_variant"])
        else:
            Animation(opacity=0, height=0, duration=0.3).start(self.timer_input_layout)
            Animation(opacity=1, height=dp(80), duration=0.3).start(self.target_input_layout)
            
            self.mode_timer_btn.md_bg_color = get_color_from_hex(self.colors["surface_container_highest"])
            self.mode_timer_btn.text_color = get_color_from_hex(self.colors["on_surface_variant"])
            self.mode_target_btn.md_bg_color = get_color_from_hex(self.colors["primary_container"])
            self.mode_target_btn.text_color = get_color_from_hex(self.colors["on_primary_container"])

    def activate_lock(self):
        """Activate lock"""
        try:
            from focus_mode_app.core.focus_lock import focus_lock

            if self.lock_mode == "timer":
                minutes = int(self.timer_entry.text or "25")
                if minutes > 0 and focus_lock.set_timer_lock(minutes):
                    self.show_dialog("Success", f"Timer: {minutes} min")
                    if not is_blocking_active():
                        toggle_blocking()
                        self.update_toggle_button()
            else:
                hour = int(self.hour_entry.text or "14")
                minute = int(self.minute_entry.text or "30")
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    if focus_lock.set_target_time_lock(hour, minute):
                        self.show_dialog("Success", f"Target: {hour:02d}:{minute:02d}")
                        if not is_blocking_active():
                            toggle_blocking()
                            self.update_toggle_button()
        except Exception as e:
            self.show_dialog("Errore", str(e))

    def _update_timer_display(self, dt):
        """Update timer display"""
        try:
            from focus_mode_app.core.focus_lock import focus_lock
            if focus_lock.is_locked():
                info = focus_lock.get_lock_info()
                self.status_label.text = f"LOCKED - {info['remaining_time']}"
                self.status_label.text_color = get_color_from_hex(self.colors["error"])
                self.toggle_btn.disabled = True
            else:
                self.status_label.text = "Nessun lock attivo"
                self.status_label.text_color = get_color_from_hex(self.colors["outline"])
                self.toggle_btn.disabled = False
        except:
            pass

    def toggle_blocking(self):
        """Toggle blocking"""
        if is_blocking_active():
            can_disable, reason = can_disable_blocking()
            if not can_disable:
                self.show_dialog("Blocco Attivo", reason)
                return

        toggle_blocking()
        self.update_toggle_button()

    def update_toggle_button(self):
        """Update toggle button"""
        if is_blocking_active():
            self.toggle_btn.text = "DISATTIVA FOCUS MODE"
            self.toggle_btn.icon = "lock"
            self.toggle_btn.md_bg_color = get_color_from_hex(self.colors["error"])
        else:
            self.toggle_btn.text = "ATTIVA FOCUS MODE"
            self.toggle_btn.icon = "lock-open"
            self.toggle_btn.md_bg_color = get_color_from_hex(self.colors["primary"])

    def set_item_type(self, item_type):
        """Set item type"""
        self.item_type = item_type
        if item_type == "app":
            self.item_desc_label.text = "Inserisci il nome dell'eseguibile (es: firefox)"
            self.type_app_btn.md_bg_color = get_color_from_hex(self.colors["primary_container"])
            self.type_app_btn.text_color = get_color_from_hex(self.colors["on_primary_container"])
            self.type_web_btn.md_bg_color = get_color_from_hex(self.colors["surface_container_highest"])
            self.type_web_btn.text_color = get_color_from_hex(self.colors["on_surface_variant"])
        else:
            self.item_desc_label.text = "Inserisci URL o dominio (es: facebook.com)"
            self.type_app_btn.md_bg_color = get_color_from_hex(self.colors["surface_container_highest"])
            self.type_app_btn.text_color = get_color_from_hex(self.colors["on_surface_variant"])
            self.type_web_btn.md_bg_color = get_color_from_hex(self.colors["primary_container"])
            self.type_web_btn.text_color = get_color_from_hex(self.colors["on_primary_container"])

    def add_item(self):
        """Add item"""
        name = self.item_entry.text.strip()
        if not name:
            return

        if self.item_type == "app":
            name = name.lower()

        if add_blocked_item(name, self.item_type):
            self.refresh_blocked_list()
            self.item_entry.text = ""
            self.show_dialog("Success", f"✓ {name} aggiunto")

    def remove_item(self, index):
        """Remove item by index"""
        items = get_blocked_items()
        if index < len(items):
            item_name = items[index]['name']
            if remove_blocked_item(index):
                # Also remove from restore if present
                try:
                    from focus_mode_app.core.session import session_tracker
                    if item_name in session_tracker.restore_list:
                        session_tracker.remove_from_restore(item_name)
                except:
                    pass
                    
                self.show_dialog("Success", f"✓ {item_name} rimosso")
                self.refresh_blocked_list()

    def toggle_item_restore(self, item_name, active):
        """Toggle restore for a specific item"""
        try:
            from focus_mode_app.core.session import session_tracker
            if active:
                session_tracker.add_to_restore(item_name)
            else:
                session_tracker.remove_from_restore(item_name)
        except Exception as e:
            self.show_dialog("Errore", str(e))

    def refresh_blocked_list(self):
        """Refresh blocked list using custom table rows"""
        self.blocked_list_container.clear_widgets()
        items = get_blocked_items()
        
        # Get current restore list
        restore_list = []
        try:
            from focus_mode_app.core.session import session_tracker
            restore_list = list(session_tracker.restore_list.keys())
        except:
            pass

        for idx, item in enumerate(items):
            icon_name = "application" if item['type'] == "app" else "web"
            item_name = item['name']
            is_restored = item_name in restore_list
            
            # Create Row
            row = MDBoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(56),
                padding=[dp(16), 0],
                spacing=dp(8),
                md_bg_color=get_color_from_hex(self.colors["surface_container"]),
                radius=[dp(8)]
            )
            
            # Col 1: Icon + Name (size_hint_x=0.5)
            col1 = MDBoxLayout(orientation='horizontal', spacing=dp(12), size_hint_x=0.5)
            
            icon = MDIcon(
                icon=icon_name,
                theme_text_color="Custom",
                text_color=get_color_from_hex(self.colors["primary"]),
                size_hint=(None, None),
                size=(dp(24), dp(24)),
                pos_hint={'center_y': .5}
            )
            
            name_label = MDLabel(
                text=item_name,
                theme_text_color="Custom",
                text_color=get_color_from_hex(self.colors["on_surface"]),
                valign="center",
                shorten=True,
                shorten_from='right'
            )
            
            col1.add_widget(icon)
            col1.add_widget(name_label)
            row.add_widget(col1)
            
            # Col 2: Checkbox (size_hint_x=0.3)
            col2 = MDBoxLayout(orientation='horizontal', size_hint_x=0.3)
            col2.add_widget(MDBoxLayout(size_hint_x=1)) # spacer
            
            checkbox = MDCheckbox(
                size_hint=(None, None),
                size=(dp(40), dp(40)),
                active=is_restored,
                pos_hint={'center_y': .5},
                selected_color=get_color_from_hex(self.colors["primary"]),
                unselected_color=get_color_from_hex(self.colors["on_surface_variant"])
            )
            checkbox.bind(active=lambda x, v, name=item_name: self.toggle_item_restore(name, v))
            
            col2.add_widget(checkbox)
            col2.add_widget(MDBoxLayout(size_hint_x=1)) # spacer
            row.add_widget(col2)
            
            # Col 3: Delete Button (size_hint_x=0.2)
            col3 = MDBoxLayout(orientation='horizontal', size_hint_x=0.2)
            col3.add_widget(MDBoxLayout(size_hint_x=1)) # spacer
            
            delete_btn = MDIconButton(
                icon="trash-can",
                theme_text_color="Custom",
                text_color=get_color_from_hex(self.colors["error"]),
                size_hint=(None, None),
                size=(dp(40), dp(40)),
                pos_hint={'center_y': .5},
                on_release=lambda x, i=idx: self.remove_item(i)
            )
            
            col3.add_widget(delete_btn)
            col3.add_widget(MDBoxLayout(size_hint_x=1)) # spacer
            row.add_widget(col3)
            
            self.blocked_list_container.add_widget(row)

    def toggle_restore(self, active):
        """Toggle global restore"""
        set_restore_enabled(active)

    def show_dialog(self, title, text):
        """Show dialog"""
        if self.current_dialog:
            self.current_dialog.dismiss()

        self.current_dialog = MDDialog(
            title=title,
            text=text,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: self.current_dialog.dismiss())]
        )
        self.current_dialog.open()


def run_app():
    """Run the app"""
    FocusModeApp().run()


if __name__ == "__main__":
    run_app()