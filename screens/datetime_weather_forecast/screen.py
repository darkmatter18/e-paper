"""All widgets screen - complete dashboard layout with system status bar.

This is the default screen showing all available widgets:
- Top: System status bar (WiFi signal, CPU temperature)
- Top-left: Analog + digital clock
- Top-right: Weather with 5-day forecast
- Bottom-left: Day and date
- Bottom-right: Quote of the day

Layout:
┌───────────────────────────────────────────────┬─────────┐
│                                               │ 📶  45°C│  ← Status bar (800x30)
├─────────────────┬─────────────────────────────┴─────────┤
│  ClockWidget    │  WeatherWidget                         │
│  (0,30,400x225) │  (400,30,400x225)                     │
├─────────────────┼────────────────────────────────────────┤
│  DateWidget     │  QuoteWidget                           │
│  (0,255,400x225)│  (400,255,400x225)                    │
└─────────────────┴────────────────────────────────────────┘
"""

from screens.datetime_weather_forecast.widgets import (
    ClockWidget,
    DateWidget,
    QuoteWidget,
    WeatherWidget,
)
from utils import Screen
from widgets import StatusBarWidget, WidgetRegion


def create_datetime_weather_forecast_screen() -> Screen:
    """Create screen with all widgets and system status bar.

    Layout aligned to 8-pixel boundaries for e-paper controller compatibility.
    All y-coordinates and dimensions divisible by 8 to prevent pixel shifts.

    Returns:
        Screen instance with status bar, clock, date, weather, and quote widgets.
    """
    return Screen(
        widgets=[
            # Status bar: y=0, height=32 (aligned)
            StatusBarWidget(WidgetRegion(x=0, y=0, width=800, height=32)),

            # Top row: y=32, height=224 (aligned)
            ClockWidget(WidgetRegion(x=0, y=32, width=400, height=224)),
            WeatherWidget(WidgetRegion(x=400, y=32, width=400, height=224)),

            # Bottom row: y=256, height=224 (aligned)
            DateWidget(WidgetRegion(x=0, y=256, width=400, height=224)),
            QuoteWidget(WidgetRegion(x=400, y=256, width=400, height=224)),
        ],
        name="Datetime Weather Forecast",
    )
