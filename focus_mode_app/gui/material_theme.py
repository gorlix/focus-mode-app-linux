"""
gui/material_theme.py
Modulo per creare interfacce Tkinter con stile Material 3.
Richiede: ttkbootstrap (pip install ttkbootstrap)
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import Listbox

# ============================================================================
# PALETTE COLORI MATERIAL 3
# ============================================================================

class MaterialColors:
    """Palette Material 3 Design (Light Theme)"""
    PRIMARY = "#6750A4"           # Viola principale
    SECONDARY = "#625B71"         # Grigio secondario
    TERTIARY = "#7D5260"          # Rosa terziario
    ERROR = "#B3261E"             # Rosso errore
    SURFACE = "#FEF7FF"           # Sfondo superficie
    SURFACE_VARIANT = "#E7E0EC"   # Variante superficie
    ON_PRIMARY = "#FFFFFF"        # Testo su primario
    ON_SURFACE = "#1C1B1F"        # Testo su superficie
    ON_SURFACE_VARIANT = "#49454F" # Testo secondario
    OUTLINE = "#79747E"           # Bordi
    SHADOW = "#000000"            # Ombre

# ============================================================================
# CONFIGURAZIONE FONT
# ============================================================================

class MaterialFonts:
    """Font Material Design (Roboto)"""
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
    """
    Applica lo stile Material 3 all'applicazione Tkinter.
    
    Args:
        root: Finestra principale Tkinter/ttkbootstrap
        theme: Tema ttkbootstrap (flatly, cosmo, litera, minty, lumen, ecc.)
    
    Returns:
        Style: Oggetto Style configurato
    """
    style = ttk.Style(theme=theme)
    
    # Configurazione generale della finestra
    root.configure(bg=MaterialColors.SURFACE)
    
    # Label
    style.configure('Material.TLabel',
                    font=MaterialFonts.BODY,
                    background=MaterialColors.SURFACE,
                    foreground=MaterialColors.ON_SURFACE)
    
    # Titoli
    style.configure('MaterialTitle.TLabel',
                    font=MaterialFonts.HEADLINE,
                    background=MaterialColors.SURFACE,
                    foreground=MaterialColors.ON_SURFACE)
    
    # Entry
    style.configure('Material.TEntry',
                    font=MaterialFonts.BODY,
                    foreground=MaterialColors.ON_SURFACE,
                    fieldbackground=MaterialColors.SURFACE_VARIANT,
                    borderwidth=1,
                    relief="flat")
    
    # Button
    style.configure('MaterialPrimary.TButton',
                    font=MaterialFonts.LABEL,
                    background=MaterialColors.PRIMARY,
                    foreground=MaterialColors.ON_PRIMARY,
                    borderwidth=0,
                    focuscolor='none',
                    padding=(16, 8))
    
    style.configure('MaterialSecondary.TButton',
                    font=MaterialFonts.LABEL,
                    background=MaterialColors.SECONDARY,
                    foreground=MaterialColors.ON_PRIMARY,
                    borderwidth=0,
                    focuscolor='none',
                    padding=(16, 8))
    
    # Frame
    style.configure('Material.TFrame',
                    background=MaterialColors.SURFACE)
    
    return style

# ============================================================================
# WIDGET HELPERS - MATERIAL 3
# ============================================================================

def material_label(master, text, style_type="body", **kwargs):
    """
    Crea una Label Material 3.
    
    Args:
        master: Parent widget
        text: Testo da mostrare
        style_type: "body" o "title"
        **kwargs: Altri argomenti per ttk.Label
    
    Returns:
        ttk.Label: Label configurata
    """
    if style_type == "title":
        label = ttk.Label(master, text=text, style='MaterialTitle.TLabel', **kwargs)
    else:
        label = ttk.Label(master, text=text, style='Material.TLabel', **kwargs)
    return label


def material_entry(master, placeholder="", **kwargs):
    """
    Crea un Entry Material 3.
    
    Args:
        master: Parent widget
        placeholder: Testo placeholder (non nativo in tkinter)
        **kwargs: Altri argomenti per ttk.Entry
    
    Returns:
        ttk.Entry: Entry configurato
    """
    entry = ttk.Entry(master, style='Material.TEntry', **kwargs)
    return entry


def material_button(master, text, command, button_type="primary", **kwargs):
    """
    Crea un Button Material 3.
    
    Args:
        master: Parent widget
        text: Testo bottone
        command: Funzione callback
        button_type: "primary" o "secondary"
        **kwargs: Altri argomenti per ttk.Button
    
    Returns:
        ttk.Button: Button configurato
    """
    if button_type == "primary":
        btn = ttk.Button(master, text=text, command=command, 
                        bootstyle="primary", **kwargs)
    else:
        btn = ttk.Button(master, text=text, command=command,
                        bootstyle="secondary", **kwargs)
    return btn


def material_listbox(master, **kwargs):
    """
    Crea una Listbox con stile Material 3.
    (Nota: Listbox standard tkinter, non ttk, quindi styling limitato)
    
    Args:
        master: Parent widget
        **kwargs: Altri argomenti per Listbox
    
    Returns:
        Listbox: Listbox configurata
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
        **kwargs
    )
    return listbox


def material_frame(master, **kwargs):
    """
    Crea un Frame Material 3.
    
    Args:
        master: Parent widget
        **kwargs: Altri argomenti per ttk.Frame
    
    Returns:
        ttk.Frame: Frame configurato
    """
    frame = ttk.Frame(master, style='Material.TFrame', **kwargs)
    return frame


def material_scrollbar(master, **kwargs):
    """
    Crea una Scrollbar Material 3.
    
    Args:
        master: Parent widget
        **kwargs: Altri argomenti per ttk.Scrollbar
    
    Returns:
        ttk.Scrollbar: Scrollbar configurata
    """
    scrollbar = ttk.Scrollbar(master, bootstyle="rounded", **kwargs)
    return scrollbar

# ============================================================================
# LAYOUT HELPERS
# ============================================================================

def add_padding(widget, padx=8, pady=8):
    """
    Aggiunge padding uniforme a un widget già creato.
    
    Args:
        widget: Widget tkinter/ttk
        padx: Padding orizzontale
        pady: Padding verticale
    """
    widget.pack_configure(padx=padx, pady=pady)


def create_card_frame(master, padx=16, pady=16):
    """
    Crea un frame "card" Material con padding e sfondo.
    
    Args:
        master: Parent widget
        padx: Padding interno orizzontale
        pady: Padding interno verticale
    
    Returns:
        ttk.Frame: Frame configurato come card
    """
    card = material_frame(master)
    card.configure(relief="flat", borderwidth=0)
    card.pack(fill="both", expand=True, padx=padx, pady=pady)
    return card

# ============================================================================
# UTILITY
# ============================================================================

def set_window_center(window, width, height):
    """
    Centra la finestra sullo schermo.
    
    Args:
        window: Finestra tkinter
        width: Larghezza finestra
        height: Altezza finestra
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
    'MaterialColors',
    'MaterialFonts',
    # Applicazione stile
    'apply_material3_style',
    # Widget factory
    'material_label',
    'material_entry',
    'material_button',
    'material_listbox',
    'material_frame',
    'material_scrollbar',
    # Layout helpers
    'add_padding',
    'create_card_frame',
    'set_window_center',
]

