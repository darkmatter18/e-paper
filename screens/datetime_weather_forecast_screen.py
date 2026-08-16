"""All widgets screen - complete dashboard layout.

This is the default screen showing all available widgets:
- Top-left: Analog + digital clock
- Top-right: Weather with 5-day forecast
- Bottom-left: Day and date
- Bottom-right: Quote of the day

Layout:
┌──────────────────┬──────────────────┐
│  ClockWidget     │  WeatherWidget   │
│  (0,0,400x240)   │  (400,0,400x240) │
├──────────────────┼──────────────────┤
│  DateWidget      │  QuoteWidget     │
│  (0,240,400x240) │  (400,240,400x240│
└──────────────────┴──────────────────┘
"""

from utils import Screen
from widgets import ClockWidget, DateWidget, QuoteWidget, WeatherWidget


def create_datetime_weather_forecast_screen() -> Screen:
    """Create screen with all widgets (current default layout).

    Returns:
        Screen instance with clock, date, weather, and quote widgets.
    """
    return Screen(
        widgets=[
            ClockWidget(),
            DateWidget(),
            WeatherWidget(),
            QuoteWidget(),
        ],
        name="Datetime Weather Forecast",
    )
