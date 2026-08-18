"""Digital clock screen - large centered time display."""

from screens.digital_clock.widgets import (
    AmPmWidget,
    ColonWidget,
    HoursWidget,
    MinutesWidget,
)
from utils.screen import Screen
from widgets import StatusBarWidget, WidgetRegion


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

            # Time components - centered on screen
            # Using generous regions, each widget centers its content within
            HoursWidget(WidgetRegion(x=100, y=150, width=180, height=200)),
            ColonWidget(WidgetRegion(x=280, y=150, width=80, height=200)),
            MinutesWidget(WidgetRegion(x=360, y=150, width=180, height=200)),

            # AM/PM offset vertically to align with text baseline
            AmPmWidget(WidgetRegion(x=540, y=220, width=140, height=130)),
        ],
    )
