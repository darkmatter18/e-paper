"""Widget system for e-paper display.

Exports:
    - Base classes from widgets.base
    - Shared widgets from widgets.shared
"""

# Base classes
from widgets.base import Widget, WidgetRegion

# Shared widgets
from widgets.shared import GuideWidget, StatusBarWidget

__all__ = [
    # Shared
    "GuideWidget",
    "StatusBarWidget",
    # Base
    "Widget",
    "WidgetRegion",
]
