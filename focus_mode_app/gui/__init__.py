"""
gui package
Contiene l'interfaccia grafica dell'applicazione con KivyMD Material You 3.
"""

from .main_window import FocusModeApp, FocusModeScreen, run_app

# Backward compatibility alias
AppGui = FocusModeApp

__all__ = [
    'FocusModeApp',
    'FocusModeScreen',
    'run_app',
    'AppGui',  # Alias per compatibilità con il vecchio codice
]