"""Centralized font path definitions.

This module provides font file paths as constants.
Widgets load fonts at their required sizes using these paths.
"""

from pathlib import Path

from settings import FONTS_DIR

# ============================================================================
# Font Paths
# ============================================================================

# Variable weight fonts
FONT_GEOMINI: Path = FONTS_DIR / "Geomini-VariableFont_wght.ttf"
FONT_PLAYFAIR: Path = FONTS_DIR / "PlayfairDisplay-VariableFont_wght.ttf"
FONT_PLAYFAIR_ITALIC: Path = FONTS_DIR / "PlayfairDisplay-Italic-VariableFont_wght.ttf"

# Regular fonts
FONT_HENNYPENNY: Path = FONTS_DIR / "HennyPenny-Regular.ttf"
FONT_RIGHTEOUS: Path = FONTS_DIR / "Righteous-Regular.ttf"

# Icon fonts
FONT_WEATHER_ICONS: Path = FONTS_DIR / "weathericons-regular-webfont.ttf"
FONT_AWESOME: Path = FONTS_DIR / "Font Awesome 7 Free-Solid-900.otf"
