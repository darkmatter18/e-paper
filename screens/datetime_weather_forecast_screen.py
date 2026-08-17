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

from utils import Screen
from widgets import (
    ClockWidget,
    DateWidget,
    QuoteWidget,
    StatusBarWidget,
    WeatherWidget,
    WidgetRegion,
)


def create_datetime_weather_forecast_screen() -> Screen:
    """Create screen with all widgets and system status bar.

    Returns:
        Screen instance with status bar, clock, date, weather, and quote widgets.
    """
    return Screen(
        widgets=[
            StatusBarWidget(WidgetRegion(x=0, y=0, width=800, height=30)),
            ClockWidget(WidgetRegion(x=0, y=30, width=400, height=225)),
            WeatherWidget(WidgetRegion(x=400, y=30, width=400, height=225)),
            DateWidget(WidgetRegion(x=0, y=255, width=400, height=225)),
            QuoteWidget(WidgetRegion(x=400, y=255, width=400, height=225)),
        ],
        name="Datetime Weather Forecast",
    )
