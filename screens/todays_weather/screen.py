"""Today's Weather screen - full-screen weather dashboard.

Comprehensive weather display with current conditions and hourly forecast graph.
Perfect for checking the day's weather at a glance.

Features:
- Large current temperature with weather icon
- Weather description
- Quick stats (feels like, humidity, wind, sunrise/sunset)
- 24-hour temperature trend line graph
- Weather icons for each forecast period
- Time labels

Widget:
- TodaysWeatherWidget (full screen 800x480)

Layout:
┌────────────────────────────────────────────────────────────────┐
│                 Current Weather - 2:30 PM                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│         ☀️              72°F          Clear Sky               │
│     (icon 64pt)     (temp 90pt RED)   (desc 32pt)             │
│                                                                │
│    Feels 70° │ 💧 45% │ 💨 8mph │ ⬆6:24AM │ ⬇7:45PM          │
│    (compact stats bar 24pt)                                   │
├────────────────────────────────────────────────────────────────┤
│                   Hourly Forecast (Next 24h)                  │
│                                                                │
│  Temperature line graph with weather icons                    │
│                                                                │
└────────────────────────────────────────────────────────────────┘

Use Case:
    Dedicated weather display for planning your day.
    Shows both current snapshot and hourly trend.
    Perfect for checking before leaving home.
"""

from screens.todays_weather.widgets import TodaysWeatherWidget
from utils import Screen


def create_todays_weather_screen() -> Screen:
    """Create full-screen today's weather dashboard.

    Returns:
        Screen instance with TodaysWeatherWidget (full screen).
    """
    return Screen(
        widgets=[
            TodaysWeatherWidget(),
        ],
        name="Today's Weather",
    )
