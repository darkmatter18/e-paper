"""Digital clock screen - large centered time display."""

from screens.digital_clock.widgets import (
    AmPmWidget,
    ColonWidget,
    HoursWidget,
    MinutesWidget,
)
from utils.screen import Screen
from widgets import GuideWidget, StatusBarWidget, WidgetRegion


def create_digital_clock_screen() -> Screen:
    """Create digital clock screen with 4 separate time widgets.

    Layout:
    - Status bar: 800x30 at top (WiFi, CPU temp)
    - Centered time display: HH:MM AM/PM in large Orbitron font
      - Hours (red): ~180px from left
      - Colon (black): ~80px separator
      - Minutes (black): ~180px, supports partial refresh
      - AM/PM (red): ~120px suffix, smaller font

    Returns:
        Screen with status bar and 4 time component widgets.
    """
    return Screen(
        name="Digital Clock",
        widgets=[
            # Status bar at top
            StatusBarWidget(WidgetRegion(x=0, y=0, width=800, height=30)),

            # Time components - properly sized for 180pt Orbitron
            # Text "88" = 300x130px, with 20px padding = 340x170px boxes
            # Total width: 340 + 85 + 340 = 765px, centered in 800px screen
            HoursWidget(WidgetRegion(x=18, y=170, width=340, height=170)),
            ColonWidget(WidgetRegion(x=358, y=170, width=85, height=170)),
            MinutesWidget(WidgetRegion(x=443, y=170, width=340, height=170)),
        ],
    )
