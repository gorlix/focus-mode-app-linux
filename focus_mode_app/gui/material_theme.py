"""
gui/material_theme.py
Focus Mode App - Material You 3 Theme Utilities
"""

import os
import sys
from kivy.utils import get_color_from_hex

class MaterialYouColors:
    """
    Provides Material You 3 color palettes.
    Can attempt to read from system (KDE Plasma) or fallback to default.
    """
    
    # Default Deep Purple Theme (Material 3)
    DEFAULT_COLORS = {
        "primary": "#BB86FC",  # Light purple for primary actions
        "on_primary": "#000000",
        "primary_container": "#3700B3",
        "on_primary_container": "#EADDFF",
        "secondary": "#03DAC6",  # Teal for secondary actions
        "on_secondary": "#000000",
        "secondary_container": "#018786",
        "on_secondary_container": "#CFBCFF",
        "tertiary": "#CF6679",  # Pinkish red for tertiary
        "on_tertiary": "#000000",
        "tertiary_container": "#B00020",
        "on_tertiary_container": "#FFD8E4",
        "error": "#CF6679",
        "on_error": "#000000",
        "error_container": "#B00020",
        "on_error_container": "#F9DEDC",
        "background": "#2B2B2B",  # Classic Darcula background
        "on_background": "#A9B7C6",  # Classic Darcula text
        "surface": "#3C3F41",  # Slightly lighter surface
        "on_surface": "#A9B7C6",
        "surface_variant": "#4E5254",
        "on_surface_variant": "#808080",
        "outline": "#808080",
        "surface_container_highest": "#45494A",
        "surface_container_high": "#3C3F41",
        "surface_container": "#313335",
        "surface_container_low": "#2B2B2B",
        "surface_container_lowest": "#1E1F22",
    }

    @staticmethod
    def get_plasma_colors():
        """
        Try to get colors from KDE Plasma configuration.
        Returns a dictionary of hex codes or None.
        """
        # For now, we return the default beautiful dark theme
        # In a real implementation, we could parse ~/.config/kdeglobals
        return MaterialYouColors.DEFAULT_COLORS

    @staticmethod
    def get_hex(color_name):
        """Get hex code for a color name"""
        return MaterialYouColors.DEFAULT_COLORS.get(color_name, "#FFFFFF")

    @staticmethod
    def get_kivy_color(color_name):
        """Get Kivy color tuple (r, g, b, a) for a color name"""
        hex_code = MaterialYouColors.get_hex(color_name)
        return get_color_from_hex(hex_code)

class MaterialFonts:
    """Material Design 3 Fonts"""
    
    STYLES = {
        "DisplayLarge": {"font_size": "57sp", "line_height": 1.12, "letter_spacing": -0.25},
        "DisplayMedium": {"font_size": "45sp", "line_height": 1.16, "letter_spacing": 0},
        "DisplaySmall": {"font_size": "36sp", "line_height": 1.22, "letter_spacing": 0},
        "HeadlineLarge": {"font_size": "32sp", "line_height": 1.25, "letter_spacing": 0},
        "HeadlineMedium": {"font_size": "28sp", "line_height": 1.29, "letter_spacing": 0},
        "HeadlineSmall": {"font_size": "24sp", "line_height": 1.33, "letter_spacing": 0},
        "TitleLarge": {"font_size": "22sp", "line_height": 1.27, "letter_spacing": 0},
        "TitleMedium": {"font_size": "16sp", "line_height": 1.5, "letter_spacing": 0.15},
        "TitleSmall": {"font_size": "14sp", "line_height": 1.43, "letter_spacing": 0.1},
        "LabelLarge": {"font_size": "14sp", "line_height": 1.43, "letter_spacing": 0.1},
        "LabelMedium": {"font_size": "12sp", "line_height": 1.33, "letter_spacing": 0.5},
        "LabelSmall": {"font_size": "11sp", "line_height": 1.45, "letter_spacing": 0.5},
        "BodyLarge": {"font_size": "16sp", "line_height": 1.5, "letter_spacing": 0.5},
        "BodyMedium": {"font_size": "14sp", "line_height": 1.43, "letter_spacing": 0.25},
        "BodySmall": {"font_size": "12sp", "line_height": 1.33, "letter_spacing": 0.4},
    }