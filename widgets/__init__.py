"""Widget system for e-paper display.

Exports:
    - Base classes from widgets.base
    - Shared widgets from widgets.shared
"""

# Base classes
from widgets.base import Widget, WidgetRegion

# Shared widgets
from widgets.shared import (
    ClockWidget,
    DateWidget,
    QuoteWidget,
    StatusBarWidget,
    WeatherWidget,
)

__all__ = [
    # Base
    "Widget",
    "WidgetRegion",
    # Shared
    "ClockWidget",
    "DateWidget",
    "QuoteWidget",
    "StatusBarWidget",
    "WeatherWidget",
]
