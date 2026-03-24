"""
gui/material_theme.py
Module for creating Tkinter interfaces with Material 3 styling.
Requires: ttkbootstrap (pip install ttkbootstrap)
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *  # noqa: F403
from tkinter import Listbox

# ============================================================================
# PALETTE COLORI MATERIAL 3
# ============================================================================


class MaterialColors:
    """Material 3 Design Palette (Light Theme)."""

    PRIMARY = "#6750A4"  # Viola principale
    SECONDARY = "#625B71"  # Grigio secondario
    TERTIARY = "#7D5260"  # Rosa terziario
    ERROR = "#B3261E"  # Rosso errore
    SURFACE = "#FEF7FF"  # Sfondo superficie
    SURFACE_VARIANT = "#E7E0EC"  # Variante superficie
    ON_PRIMARY = "#FFFFFF"  # Testo su primario
    ON_SURFACE = "#1C1B1F"  # Testo su superficie
    ON_SURFACE_VARIANT = "#49454F"  # Testo secondario
    OUTLINE = "#79747E"  # Bordi
    SHADOW = "#000000"  # Ombre


# ============================================================================
# CONFIGURAZIONE FONT
# ============================================================================


class MaterialFonts:
    """Material Design Fonts (Roboto)."""

    DISPLAY = ("Roboto", 24, "bold")
    HEADLINE = ("Roboto", 18, "bold")
    TITLE = ("Roboto", 16, "bold")
    BODY = ("Roboto", 14)
    LABEL = ("Roboto", 12, "bold")
    CAPTION = ("Roboto", 11)


# ============================================================================
# APPLICAZIONE STILE GLOBALE
# ============================================================================


def apply_material3_style(root, theme="flatly"):
    """Apply the Material 3 style to the main Tkinter application.

    Args:
        root: The main Tkinter/ttkbootstrap window instance.
        theme (str): Background ttkbootstrap theme to base off (e.g., flatly).

    Returns:
        ttk.Style: The configured Style object.
    """
    style = ttk.Style(theme=theme)

    # Configurazione generale della finestra
    root.configure(bg=MaterialColors.SURFACE)

    # Label
    style.configure(
        "Material.TLabel",
        font=MaterialFonts.BODY,
        background=MaterialColors.SURFACE,
        foreground=MaterialColors.ON_SURFACE,
    )

    # Titoli
    style.configure(
        "MaterialTitle.TLabel",
        font=MaterialFonts.HEADLINE,
        background=MaterialColors.SURFACE,
        foreground=MaterialColors.ON_SURFACE,
    )

    # Entry
    style.configure(
        "Material.TEntry",
        font=MaterialFonts.BODY,
        foreground=MaterialColors.ON_SURFACE,
        fieldbackground=MaterialColors.SURFACE_VARIANT,
        borderwidth=1,
        relief="flat",
    )

    # Button
    style.configure(
        "MaterialPrimary.TButton",
        font=MaterialFonts.LABEL,
        background=MaterialColors.PRIMARY,
        foreground=MaterialColors.ON_PRIMARY,
        borderwidth=0,
        focuscolor="none",
        padding=(16, 8),
    )

    style.configure(
        "MaterialSecondary.TButton",
        font=MaterialFonts.LABEL,
        background=MaterialColors.SECONDARY,
        foreground=MaterialColors.ON_PRIMARY,
        borderwidth=0,
        focuscolor="none",
        padding=(16, 8),
    )

    # Frame
    style.configure("Material.TFrame", background=MaterialColors.SURFACE)

    return style


# ============================================================================
# WIDGET HELPERS - MATERIAL 3
# ============================================================================


def material_label(master, text, style_type="body", **kwargs):
    """Create a Material 3 styled Label.

    Args:
        master: The parent widget.
        text (str): The text to display.
        style_type (str): "body" or "title" to dictate font scale.
        **kwargs: Additional arguments for ttk.Label.

    Returns:
        ttk.Label: The configured Label widget.
    """
    if style_type == "title":
        label = ttk.Label(master, text=text, style="MaterialTitle.TLabel", **kwargs)
    else:
        label = ttk.Label(master, text=text, style="Material.TLabel", **kwargs)
    return label


def material_entry(master, placeholder="", **kwargs):
    """Create a Material 3 styled Entry field.

    Args:
        master: The parent widget.
        placeholder (str): Placeholder text (Note: not native to core tkinter).
        **kwargs: Additional arguments for ttk.Entry.

    Returns:
        ttk.Entry: The configured Entry widget.
    """
    entry = ttk.Entry(master, style="Material.TEntry", **kwargs)
    return entry


def material_button(master, text, command, button_type="primary", **kwargs):
    """Create a Material 3 styled Button.

    Args:
        master: The parent widget.
        text (str): Button text.
        command (Callable): The callback function to execute on click.
        button_type (str): "primary" or "secondary".
        **kwargs: Additional arguments for ttk.Button.

    Returns:
        ttk.Button: The configured Button widget.
    """
    if button_type == "primary":
        btn = ttk.Button(
            master, text=text, command=command, bootstyle="primary", **kwargs
        )
    else:
        btn = ttk.Button(
            master, text=text, command=command, bootstyle="secondary", **kwargs
        )
    return btn


def material_listbox(master, **kwargs):
    """Create a Listbox with Material 3 styling.

    Note: Uses standard tkinter Listbox (not ttk), so styling is limited to colors and fonts.

    Args:
        master: The parent widget.
        **kwargs: Additional arguments for Listbox.

    Returns:
        Listbox: The configured Listbox widget.
    """
    listbox = Listbox(
        master,
        font=MaterialFonts.BODY,
        bg=MaterialColors.SURFACE_VARIANT,
        fg=MaterialColors.ON_SURFACE,
        selectbackground=MaterialColors.PRIMARY,
        selectforeground=MaterialColors.ON_PRIMARY,
        bd=0,
        highlightthickness=0,
        relief="flat",
        **kwargs,
    )
    return listbox


def material_frame(master, **kwargs):
    """Create a Material 3 styled Frame.

    Args:
        master: The parent widget.
        **kwargs: Additional arguments for ttk.Frame.

    Returns:
        ttk.Frame: The configured Frame widget.
    """
    frame = ttk.Frame(master, style="Material.TFrame", **kwargs)
    return frame


def material_scrollbar(master, **kwargs):
    """Create a Material 3 styled Scrollbar.

    Args:
        master: The parent widget.
        **kwargs: Additional arguments for ttk.Scrollbar.

    Returns:
        ttk.Scrollbar: The configured Scrollbar widget.
    """
    scrollbar = ttk.Scrollbar(master, bootstyle="rounded", **kwargs)
    return scrollbar


# ============================================================================
# LAYOUT HELPERS
# ============================================================================


def add_padding(widget, padx=8, pady=8):
    """Add uniform padding to an already created widget using pack_configure.

    Args:
        widget: The tkinter/ttk widget.
        padx (int): Horizontal padding.
        pady (int): Vertical padding.
    """
    widget.pack_configure(padx=padx, pady=pady)


def create_card_frame(master, padx=16, pady=16):
    """Create a Material "card" frame with padding and background.

    Args:
        master: The parent widget.
        padx (int): Internal horizontal padding.
        pady (int): Internal vertical padding.

    Returns:
        ttk.Frame: The Frame configured as a card.
    """
    card = material_frame(master)
    card.configure(relief="flat", borderwidth=0)
    card.pack(fill="both", expand=True, padx=padx, pady=pady)
    return card


# ============================================================================
# UTILITY
# ============================================================================


def set_window_center(window, width, height):
    """Center a Tkinter window on the primary screen.

    Args:
        window: The Tkinter window instance.
        width (int): Target width of the window.
        height (int): Target height of the window.
    """
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    # Classi colori e font
    "MaterialColors",
    "MaterialFonts",
    # Applicazione stile
    "apply_material3_style",
    # Widget factory
    "material_label",
    "material_entry",
    "material_button",
    "material_listbox",
    "material_frame",
    "material_scrollbar",
    # Layout helpers
    "add_padding",
    "create_card_frame",
    "set_window_center",
]
