"""All widgets screen - complete dashboard layout with system status bar.

This is the default screen showing all available widgets:
- Top: System status bar (WiFi, CPU temperature)
- Top-left: Analog + digital clock
- Top-right: Weather with 5-day forecast
- Bottom-left: Day and date
- Bottom-right: Quote of the day

Layout:
┌─────────────────────────────────────┬───────────┐
│                                     │ 📶  45°C  │  ← Status bar (800x40)
├─────────────────┬───────────────────┴───────────┤
│  ClockWidget    │  WeatherWidget                │
│  (0,40,400x220) │  (400,40,400x220)            │
├─────────────────┼───────────────────────────────┤
│  DateWidget     │  QuoteWidget                  │
│  (0,260,400x220)│  (400,260,400x220)           │
└─────────────────┴───────────────────────────────┘
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
            StatusBarWidget(WidgetRegion(x=0, y=0, width=800, height=40)),
            ClockWidget(WidgetRegion(x=0, y=40, width=400, height=220)),
            WeatherWidget(WidgetRegion(x=400, y=40, width=400, height=220)),
            DateWidget(WidgetRegion(x=0, y=260, width=400, height=220)),
            QuoteWidget(WidgetRegion(x=400, y=260, width=400, height=220)),
        ],
        name="Datetime Weather Forecast",
    )
