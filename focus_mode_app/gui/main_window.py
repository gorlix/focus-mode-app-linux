"""
gui/main_window.py
Main window of the Focus Mode App.
Manages the user interface for configuring blocked apps and webapps.
Integrates the auto-restore management panel.
Integrates the focus lock timer and target time to prevent premature deactivation.
"""

from tkinter import messagebox
import ttkbootstrap as ttk

from focus_mode_app.config import WINDOW_WIDTH, WINDOW_HEIGHT, GUI_THEME, APP_TITLE
from focus_mode_app.core.blocker import (
    is_blocking_active,
    toggle_blocking,
    set_restore_enabled,
    is_restore_enabled,
    can_disable_blocking,
)
from focus_mode_app.core.storage import (
    add_blocked_item,
    remove_blocked_item,
    get_blocked_items,
)
from focus_mode_app.utils.tray_icon import update_tray_menu
from focus_mode_app.gui.material_theme import (
    apply_material3_style,
    material_label,
    material_entry,
    material_button,
    material_listbox,
    create_card_frame,
    set_window_center,
    MaterialColors,
)


class AppGui(ttk.Window):
    """Main window of the Focus Mode App.

    Manages the user interface for configuring blocked apps and webapps.
    Includes the auto-restore applications management panel.
    Includes the focus lock timer and target time for concentrated sessions.
    """

    def __init__(self) -> None:
        """Initialize the main window with the Material 3 theme and layout."""
        super().__init__(themename=GUI_THEME)

        self.title(APP_TITLE)

        set_window_center(self, WINDOW_WIDTH, WINDOW_HEIGHT)

        apply_material3_style(self)

        self._create_widgets()

        self.refresh_list()

        self.protocol("WM_DELETE_WINDOW", self.hide_window)

    # ========================================================================
    # UI CREATION
    # ========================================================================

    def _create_widgets(self) -> None:
        """Create all widgets for the main interface."""
        main_frame = create_card_frame(self, padx=24, pady=24)

        self._create_title(main_frame)
        self._create_toggle_button(main_frame)
        self._create_timer_panel(main_frame)
        self._create_restore_panel(main_frame)
        self._create_blocked_section(main_frame)
        self._create_feedback_label(main_frame)
        self._create_action_buttons(main_frame)

    def _create_title(self, parent: ttk.Frame) -> None:
        """Create the main title of the interface.

        Args:
            parent (ttk.Frame): The parent widget frame.
        """
        title = material_label(parent, "Focus Mode App", style_type="title")
        title.pack(pady=(0, 10))

    def _create_toggle_button(self, parent: ttk.Frame) -> None:
        """Create the toggle button to activate or deactivate the blocker.

        Args:
            parent (ttk.Frame): The parent widget frame.
        """
        self.toggle_btn = ttk.Button(
            parent,
            text="ACTIVATE STUDY MODE",
            command=self.toggle_blocking,
            bootstyle="success-outline",
            width=30,
        )
        self.toggle_btn.pack(pady=(0, 20))

    def _create_timer_panel(self, parent: ttk.Frame) -> None:
        """Create the timer/target time panel for focus lock.

        Allows the user to set a countdown timer or a target time.

        Args:
            parent (ttk.Frame): The parent widget frame.
        """
        timer_frame = ttk.LabelFrame(
            parent, text="FOCUS LOCK", bootstyle="warning", padding=16
        )
        timer_frame.pack(fill="x", pady=(0, 16))

        # Radio buttons to choose the mode
        mode_frame = ttk.Frame(timer_frame)
        mode_frame.pack(fill="x", pady=(0, 8))

        self.lock_mode = ttk.StringVar(value="timer")

        radio_timer = ttk.Radiobutton(
            mode_frame,
            text="⏲️ Timer (minutes)",
            variable=self.lock_mode,
            value="timer",
            bootstyle="warning",
            command=self.update_lock_input_visibility,
        )
        radio_timer.pack(side="left", padx=(0, 16))

        radio_target = ttk.Radiobutton(
            mode_frame,
            text="🕐 Target Time",
            variable=self.lock_mode,
            value="target",
            bootstyle="warning",
            command=self.update_lock_input_visibility,
        )
        radio_target.pack(side="left")

        # Timer input frame
        self.timer_input_frame = ttk.Frame(timer_frame)
        self.timer_input_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(self.timer_input_frame, text="Minutes:").pack(
            side="left", padx=(0, 8)
        )

        self.timer_entry = ttk.Entry(self.timer_input_frame, width=10)
        self.timer_entry.pack(side="left", padx=(0, 8))
        self.timer_entry.insert(0, "25")

        # Target time input frame
        self.target_input_frame = ttk.Frame(timer_frame)

        ttk.Label(self.target_input_frame, text="Time:").pack(side="left", padx=(0, 8))

        self.target_hour_entry = ttk.Entry(self.target_input_frame, width=5)
        self.target_hour_entry.pack(side="left", padx=(0, 4))
        self.target_hour_entry.insert(0, "14")

        ttk.Label(self.target_input_frame, text=":").pack(side="left", padx=2)

        self.target_minute_entry = ttk.Entry(self.target_input_frame, width=5)
        self.target_minute_entry.pack(side="left", padx=(4, 8))
        self.target_minute_entry.insert(0, "30")

        ttk.Label(self.target_input_frame, text="(HH:MM)").pack(
            side="left", padx=(0, 8)
        )

        # Activate lock button
        self.btn_activate_lock = material_button(
            timer_frame, "Activate Lock", self.activate_lock, button_type="warning"
        )
        self.btn_activate_lock.pack(fill="x", pady=(0, 8))

        # Status label
        self.timer_status_label = ttk.Label(
            timer_frame,
            text="No active lock",
            font=("Roboto", 11, "bold"),
            foreground="gray",
        )
        self.timer_status_label.pack()

        # Set initial visibility
        self.update_lock_input_visibility()

        # Start update loop
        self.update_timer_display()

    def update_lock_input_visibility(self) -> None:
        """Show or hide input fields based on the selected mode."""
        if self.lock_mode.get() == "timer":
            self.timer_input_frame.pack(fill="x", pady=(0, 8))
            self.target_input_frame.pack_forget()
        else:
            self.timer_input_frame.pack_forget()
            self.target_input_frame.pack(fill="x", pady=(0, 8))

    def activate_lock(self) -> None:
        """Activate the focus lock in timer or target time mode."""
        try:
            from focus_mode_app.core.focus_lock import focus_lock

            mode = self.lock_mode.get()

            if mode == "timer":
                minutes = int(self.timer_entry.get())

                if minutes <= 0:
                    self.show_feedback("Enter minutes > 0")
                    return

                if focus_lock.set_timer_lock(minutes):
                    self.show_feedback(f"Timer Lock activated: {minutes} min")
                else:
                    self.show_feedback("Error activating timer")
                    return

            else:
                hour = int(self.target_hour_entry.get())
                minute = int(self.target_minute_entry.get())

                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    self.show_feedback("Invalid time (HH: 0-23, MM: 0-59)")
                    return

                if focus_lock.set_target_time_lock(hour, minute):
                    self.show_feedback(f"Target Time Lock: {hour:02d}:{minute:02d}")
                else:
                    self.show_feedback("Error activating target time")
                    return

            if not is_blocking_active():
                toggle_blocking()
                self.update_toggle_button()

        except ValueError:
            self.show_feedback("Enter valid numerical values")
        except Exception as e:
            self.show_feedback(f"Error: {e}")

    def update_timer_display(self) -> None:
        """Update the timer display every second.

        Shows the countdown and manages the state of the disable button.
        """
        try:
            from focus_mode_app.core.focus_lock import focus_lock

            if focus_lock.is_locked():
                info = focus_lock.get_lock_info()
                self.timer_status_label.config(
                    text=f"LOCKED - {info['remaining_time']} remaining",
                    foreground="red",
                )

                if is_blocking_active():
                    self.toggle_btn.config(state="disabled")
            else:
                self.timer_status_label.config(text="No active lock", foreground="gray")

                self.toggle_btn.config(state="normal")

        except ImportError:
            pass
        except Exception as e:
            print(f"[ERROR] Timer display update: {e}")

        self.after(1000, self.update_timer_display)

    def _create_restore_panel(self, parent: ttk.Frame) -> None:
        """Create the panel for managing auto-restore applications.

        Allows the user to select which applications should be automatically
        re-launched when the blocking is disabled.

        Args:
            parent (ttk.Frame): The parent widget frame.
        """
        restore_frame = ttk.LabelFrame(
            parent, text="AUTO-RESTORE ON DISABLE", bootstyle="info", padding=16
        )
        restore_frame.pack(fill="both", expand=False, pady=(0, 16))

        self.restore_listbox = material_listbox(restore_frame, height=3)
        self.restore_listbox.pack(fill="both", expand=True, pady=(0, 8))

        restore_btn_frame = ttk.Frame(restore_frame)
        restore_btn_frame.pack(fill="x", pady=(0, 8))

        btn_add_restore = material_button(
            restore_btn_frame, "Add to Restore", self.add_to_restore, button_type="info"
        )
        btn_add_restore.pack(side="left", expand=True, fill="x", padx=(0, 4))

        btn_remove_restore = ttk.Button(
            restore_btn_frame,
            text="Remove",
            command=self.remove_from_restore,
            bootstyle="danger",
        )
        btn_remove_restore.pack(side="right", expand=True, fill="x", padx=(4, 0))

        self.restore_toggle_frame = ttk.Frame(restore_frame)
        self.restore_toggle_frame.pack(fill="x")

        self.restore_toggle_btn = ttk.Button(
            self.restore_toggle_frame,
            text="SUSPEND AUTO-RESTORE",
            command=self.toggle_restore_enabled,
            bootstyle="warning-outline",
        )
        self.restore_toggle_btn.pack(fill="x")

        self.refresh_restore_list()

    def _create_blocked_section(self, parent: ttk.Frame) -> None:
        """Create the section to manage blocked items (apps and webapps).

        Args:
            parent (ttk.Frame): The parent widget frame.
        """
        section = ttk.LabelFrame(
            parent, text="Blocked Items", bootstyle="primary", padding=16
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

    def _create_type_selector(self, parent: ttk.Frame) -> None:
        """Create radio buttons to select the type (native app or webapp).

        Args:
            parent (ttk.Frame): The parent widget frame.
        """
        radio_frame = ttk.Frame(parent)
        radio_frame.pack(fill="x", pady=(0, 12))

        self.item_type = ttk.StringVar(value="app")

        radio_app = ttk.Radiobutton(
            radio_frame,
            text="Native App",
            variable=self.item_type,
            value="app",
            bootstyle="primary",
        )
        radio_app.pack(side="left", padx=(0, 16))

        radio_webapp = ttk.Radiobutton(
            radio_frame,
            text="Webapp",
            variable=self.item_type,
            value="webapp",
            bootstyle="info",
        )
        radio_webapp.pack(side="left")

        self.item_type.trace_add("write", lambda *args: self.update_description())

    def _create_item_buttons(self, parent: ttk.Frame) -> None:
        """Create buttons to add and remove items from the blocklist.

        Args:
            parent (ttk.Frame): The parent widget frame.
        """
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", pady=(0, 8))

        btn_add = material_button(
            btn_frame, "Add", self.add_item, button_type="primary"
        )
        btn_add.pack(side="left", expand=True, fill="x", padx=(0, 4))

        btn_remove = ttk.Button(
            btn_frame, text="Remove", command=self.remove_item, bootstyle="danger"
        )
        btn_remove.pack(side="right", expand=True, fill="x", padx=(4, 0))

    def _create_feedback_label(self, parent: ttk.Frame) -> None:
        """Create the label to display temporary feedback messages.

        Args:
            parent (ttk.Frame): The parent widget frame.
        """
        self.feedback_label = ttk.Label(
            parent,
            text="",
            font=("Roboto", 11),
            foreground=MaterialColors.PRIMARY,
            background=MaterialColors.SURFACE,
        )
        self.feedback_label.pack(pady=(8, 0))

    def _create_action_buttons(self, parent: ttk.Frame) -> None:
        """Create the main action buttons (refresh, quit).

        Args:
            parent (ttk.Frame): The parent widget frame.
        """
        actions_frame = ttk.Frame(parent)
        actions_frame.pack(fill="x", pady=(8, 0))

        btn_refresh = material_button(
            actions_frame, "Refresh", self.refresh_list, button_type="secondary"
        )
        btn_refresh.pack(side="left", expand=True, fill="x", padx=(0, 4))

        btn_quit = ttk.Button(
            actions_frame, text="Quit", command=self.quit_app, bootstyle="danger"
        )
        btn_quit.pack(side="right", expand=True, fill="x", padx=(4, 0))

    # ========================================================================
    # BLOCKING MANAGEMENT
    # ========================================================================

    def toggle_blocking(self) -> None:
        """Toggle the block and update the interface.

        Also manages auto-restore upon deactivation.
        Checks focus lock status before disabling.
        """
        if is_blocking_active():
            can_disable, reason = can_disable_blocking()
            if not can_disable:
                self.show_feedback(f"{reason}")
                return

        toggle_blocking()
        self.update_toggle_button()

        update_tray_menu()

    def update_toggle_button(self) -> None:
        """Update the text and style of the toggle button based on state."""
        if is_blocking_active():
            self.toggle_btn.config(text="DEACTIVATE STUDY MODE", bootstyle="danger")
            self.show_feedback("Study Mode ACTIVATED - Apps will be blocked")
        else:
            self.toggle_btn.config(
                text="ACTIVATE STUDY MODE", bootstyle="success-outline"
            )
            self.show_feedback("Study Mode DEACTIVATED - No active blocks")

    # ========================================================================
    # RESTORE MANAGEMENT
    # ========================================================================

    def add_to_restore(self) -> None:
        """Add the selected app from the blocklist to the restore list.

        Uses get_blocked_items() for correct synchronization.
        """
        selection = self.listbox.curselection()
        if not selection:
            self.show_feedback("Select an app first")
            return

        index = selection[0]
        items = get_blocked_items()

        if index >= len(items):
            print(f"[ERROR] Index {index} out of range (len={len(items)})")
            self.show_feedback("Error: item not found")
            self.refresh_list()
            return

        app_name = items[index]["name"]

        try:
            from focus_mode_app.core.session import session_tracker

            session_tracker.add_to_restore(app_name)
            self.refresh_restore_list()
            self.show_feedback(f"Added {app_name} to restore!")
        except Exception as e:
            print(f"[ERROR] Add to restore: {e}")
            self.show_feedback(f"Error: {e}")

    def remove_from_restore(self) -> None:
        """Remove the selected app from the restore list."""
        selection = self.restore_listbox.curselection()
        if not selection:
            self.show_feedback("Select an app first")
            return

        try:
            from focus_mode_app.core.session import session_tracker

            app_names = list(session_tracker.restore_list.keys())
            if selection[0] >= len(app_names):
                self.show_feedback("Error: item not found")
                return

            app_name = app_names[selection[0]]

            session_tracker.remove_from_restore(app_name)
            self.refresh_restore_list()
            self.show_feedback(f"Removed {app_name} from restore!")
        except Exception as e:
            print(f"[ERROR] Remove from restore: {e}")
            self.show_feedback(f"Error: {e}")

    def refresh_restore_list(self) -> None:
        """Refresh the listbox with applications to be restored."""
        self.restore_listbox.delete(0, ttk.END)

        try:
            from focus_mode_app.core.session import session_tracker

            for app_name in session_tracker.restore_list.keys():
                self.restore_listbox.insert(ttk.END, f"{app_name}")
        except Exception as e:
            print(f"[ERROR] Refresh restore list: {e}")

    def toggle_restore_enabled(self) -> None:
        """Toggle the auto-restore state for the current session.

        Allows the user to disable restore functionality on the fly.
        """
        current_state = is_restore_enabled()
        new_state = not current_state

        set_restore_enabled(new_state)

        if new_state:
            self.restore_toggle_btn.config(
                text="SUSPEND AUTO-RESTORE", bootstyle="warning-outline"
            )
            self.show_feedback("Auto-restore ENABLED")
        else:
            self.restore_toggle_btn.config(
                text="ENABLE AUTO-RESTORE", bootstyle="success-outline"
            )
            self.show_feedback("Auto-restore DISABLED")

    # ========================================================================
    # BLOCKED ITEMS MANAGEMENT
    # ========================================================================

    def update_description(self) -> None:
        """Update the descriptive text based on the selected item type."""
        if self.item_type.get() == "app":
            self.desc_label.config(text="Executable name (e.g., firefox, telegram):")
        else:
            self.desc_label.config(
                text="URL or command string (e.g., web.whatsapp.com):"
            )

    def add_item(self) -> None:
        """Add an item to the blocklist.

        Normalizes the name and saves it to disk.
        """
        name = self.entry.get().strip()
        item_type = self.item_type.get()

        if item_type == "app":
            name = name.lower()

        if not name:
            self.show_feedback("Enter a valid value")
            return

        if add_blocked_item(name, item_type):
            self.listbox.insert(ttk.END, f"{name}")
            self.show_feedback(f"Added and saved: {name}")
            self.entry.delete(0, ttk.END)
        else:
            self.show_feedback("Item already exists or is invalid")

    def remove_item(self) -> None:
        """Remove the selected item from the blocklist.

        Updates both the UI and persistent storage.
        Uses get_blocked_items() for correct synchronization.
        """
        selection = self.listbox.curselection()
        if not selection:
            self.show_feedback("Select an item to remove")
            return

        index = selection[0]
        items = get_blocked_items()

        if index >= len(items):
            self.show_feedback("Error: item not found")
            self.refresh_list()
            return

        item_name = items[index]["name"]

        if remove_blocked_item(index):
            self.listbox.delete(index)
            self.show_feedback(f"Removed: {item_name}")
        else:
            self.show_feedback("Error during removal")

    def refresh_list(self) -> None:
        """Refresh the listbox with all saved items.

        Synchronizes the interface with persistent storage.
        Uses get_blocked_items() for up-to-date data.
        """
        self.listbox.delete(0, ttk.END)

        items = get_blocked_items()

        for item in items:
            self.listbox.insert(ttk.END, f"{item['name']}")

        self.show_feedback(f"Blocked items: {len(items)}")

    # ========================================================================
    # FEEDBACK AND WINDOW MANAGEMENT
    # ========================================================================

    def show_feedback(self, message: str, duration: int = 3000) -> None:
        """Show a temporary feedback message in the GUI.

        The message disappears automatically after the specified duration.

        Args:
            message (str): Text of the message.
            duration (int): Duration in milliseconds before it vanishes.
        """
        self.feedback_label.config(text=message)
        self.after(duration, lambda: self.feedback_label.config(text=""))

    def hide_window(self) -> None:
        """Hide the main window (minimize to system tray).

        The application continues running in the background.
        """
        self.withdraw()
        print("[INFO] Window hidden")

    def quit_app(self) -> None:
        """Completely exit the application with a confirmation dialog.

        Saves the configuration before exiting.
        """
        if messagebox.askokcancel("Quit", "Do you want to exit the Focus Mode App?"):
            print("[INFO] Application closure requested")
            self.quit()
