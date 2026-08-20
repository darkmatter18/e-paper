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

            # Time components - ALIGNED TO 8-PIXEL BOUNDARIES
            # E-paper controllers use byte (8-pixel) memory boundaries
            # Misaligned regions cause pixel shifts and border fading
            # All x-coordinates and widths MUST be divisible by 8
            HoursWidget(WidgetRegion(x=16, y=168, width=344, height=176)),
            ColonWidget(WidgetRegion(x=360, y=168, width=88, height=176)),
            MinutesWidget(WidgetRegion(x=448, y=168, width=344, height=176)),
        ],
    )
