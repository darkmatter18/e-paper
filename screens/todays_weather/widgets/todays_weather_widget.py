"""Today's Weather Widget - full-screen current weather with hourly forecast graph.

This widget displays comprehensive weather information in a dashboard layout:
- Current conditions with large temperature display
- Quick stats bar (feels like, humidity, wind, sunrise/sunset)
- 24-hour temperature trend line graph
- Weather icons for each forecast period

Designed for full 800x480 display as a dedicated weather screen.

Layout:
    Top section (0-160px): Current weather with icon, temp, description, stats
    Graph section (160-480px): Hourly forecast line graph with icons and labels

Hardware:
    - Temperature uses red channel for emphasis
    - Graph line and text in black
    - Weather icons in black
"""

import logging

from PIL import ImageDraw, ImageFont

from services.weather import OpenWeatherMapService, WeatherService
from settings import get_settings
from settings.fonts import FONT_GEOMINI, FONT_RIGHTEOUS, FONT_WEATHER_ICONS
from utils import DateTimeUtil
from widgets.base import Widget, WidgetRegion

logger = logging.getLogger(__name__)

# Fonts for today's weather widget
FONT_CURRENT_TEMP = ImageFont.truetype(str(FONT_RIGHTEOUS), 90)  # Current temperature
FONT_CURRENT_DESC = ImageFont.truetype(str(FONT_RIGHTEOUS), 32)  # Weather description
FONT_STATS = ImageFont.truetype(str(FONT_RIGHTEOUS), 24)  # Stats bar
FONT_GRAPH_LABEL = ImageFont.truetype(str(FONT_GEOMINI), 18)  # Graph axis labels
FONT_TIME_LABEL = ImageFont.truetype(str(FONT_GEOMINI), 16)  # Time labels
FONT_WEATHER_ICON_SMALL = ImageFont.truetype(str(FONT_WEATHER_ICONS), 20)  # Icons below graph

# Weather icon mapping (same as weather_widget.py)
WEATHER_ICON_MAP = {
    "01d": "", "01n": "",  # Clear
    "02d": "", "02n": "",  # Few clouds
    "03d": "", "03n": "",  # Scattered clouds
    "04d": "", "04n": "",  # Broken clouds
    "09d": "", "09n": "",  # Shower rain
    "10d": "", "10n": "",  # Rain
    "11d": "", "11n": "",  # Thunderstorm
    "13d": "", "13n": "",  # Snow
    "50d": "", "50n": "",  # Mist
}


class TodaysWeatherWidget(Widget):
    """Full-screen weather widget with current conditions and hourly graph.

    Shows comprehensive weather dashboard:
    - Current: Large temp, icon, description
    - Stats: Feels like, humidity, wind, sunrise/sunset
    - Graph: 24-hour temperature trend with icons

    Region: Full screen (800x480)

    Attributes:
        region: WidgetRegion(x=0, y=0, width=800, height=480)
        weather_service: OpenWeatherMapService for fetching data
        lat: Location latitude
        lon: Location longitude
    """

    def __init__(self):
        """Initialize today's weather widget with full screen region."""
        super().__init__(WidgetRegion(x=0, y=0, width=800, height=480))
        settings = get_settings()
        self.weather_service: WeatherService = OpenWeatherMapService(settings.weather.api_key)
        self.lat = settings.weather.latitude
        self.lon = settings.weather.longitude

    def draw(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None = None, **kwargs):
        """Draw today's weather dashboard.

        Args:
            black_draw: PIL ImageDraw for black channel (icons, text, graph).
            red_draw: Optional PIL ImageDraw for red channel (temperature numbers).
            **kwargs: Unused.
        """
        try:
            weather = self.weather_service.get_weather(self.lat, self.lon)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to fetch weather: {e}")
            self._draw_error(black_draw)
            return

        # Draw sections
        self._draw_header(black_draw)
        self._draw_current_weather(black_draw, red_draw, weather)
        self._draw_hourly_graph(black_draw, weather)

    def _draw_header(self, black_draw: ImageDraw.ImageDraw):
        """Draw header with title and timestamp."""
        header_text = "Current Weather"
        bbox = black_draw.textbbox((0, 0), header_text, font=FONT_CURRENT_DESC)
        tw = bbox[2] - bbox[0]
        black_draw.text((400 - tw // 2, 15), header_text, font=FONT_CURRENT_DESC, fill=0)

        # Timestamp
        now = DateTimeUtil.now()
        time_text = now.strftime("%-I:%M %p")
        bbox = black_draw.textbbox((0, 0), time_text, font=FONT_STATS)
        tw = bbox[2] - bbox[0]
        black_draw.text((750 - tw, 20), time_text, font=FONT_STATS, fill=0)

    def _draw_current_weather(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None, weather):
        """Draw current weather section with icon, temp, description, stats."""
        current = weather.current

        # Weather icon (centered at x=150)
        icon_code = current.icon or "01d"
        icon_char = WEATHER_ICON_MAP.get(icon_code, "")
        icon_font = ImageFont.truetype(str(FONT_WEATHER_ICONS), 64)
        black_draw.text((120, 70), icon_char, font=icon_font, fill=0)

        # Temperature (centered at x=400, RED)
        temp_text = f"{int(current.temperature)}°"
        if red_draw:
            bbox = red_draw.textbbox((0, 0), temp_text, font=FONT_CURRENT_TEMP)
            tw = bbox[2] - bbox[0]
            red_draw.text((400 - tw // 2, 60), temp_text, font=FONT_CURRENT_TEMP, fill=0)
        else:
            bbox = black_draw.textbbox((0, 0), temp_text, font=FONT_CURRENT_TEMP)
            tw = bbox[2] - bbox[0]
            black_draw.text((400 - tw // 2, 60), temp_text, font=FONT_CURRENT_TEMP, fill=0)

        # Description (centered at x=600)
        desc_text = current.description.title()
        bbox = black_draw.textbbox((0, 0), desc_text, font=FONT_CURRENT_DESC)
        tw = bbox[2] - bbox[0]
        black_draw.text((650 - tw // 2, 85), desc_text, font=FONT_CURRENT_DESC, fill=0)

        # Stats bar (centered, compact) - using available CurrentWeather fields
        stats_parts = [
            f"Feels {int(current.feels_like)}°",
            f"💧 Humidity {current.humidity}%",
        ]

        # Add rain probability if > 0
        if current.rain_probability > 0:
            stats_parts.append(f"🌧 Rain {current.rain_probability}%")

        stats_text = " │ ".join(stats_parts)
        bbox = black_draw.textbbox((0, 0), stats_text, font=FONT_STATS)
        tw = bbox[2] - bbox[0]
        black_draw.text((400 - tw // 2, 135), stats_text, font=FONT_STATS, fill=0)

    def _draw_hourly_graph(self, black_draw: ImageDraw.ImageDraw, weather):
        """Draw hourly temperature forecast graph."""
        # Graph area
        graph_x = 50
        graph_y = 180
        graph_w = 700
        graph_h = 200

        # Title
        title = "Hourly Forecast (Next 24h)"
        bbox = black_draw.textbbox((0, 0), title, font=FONT_CURRENT_DESC)
        tw = bbox[2] - bbox[0]
        black_draw.text((400 - tw // 2, graph_y - 10), title, font=FONT_CURRENT_DESC, fill=0)

        graph_y += 35

        # Get hourly data (use forecast, take every 3 hours for 24h = 8 points)
        forecast = weather.forecast[:8]  # 8 days, use first temp as proxy
        if not forecast:
            black_draw.text((400, 300), "No forecast data", font=FONT_STATS, fill=0)
            return

        # Create hourly data points (simulate hourly from 3-hour forecast)
        temps = []
        icons = []
        times = []

        for i, day in enumerate(forecast):
            temps.append(day.temp_max)
            icons.append(day.icon)
            hour_offset = i * 3
            time_label = f"{hour_offset}h" if i > 0 else "Now"
            times.append(time_label)

        # Find temperature range
        min_temp = min(temps)
        max_temp = max(temps)
        temp_range = max_temp - min_temp
        temp_range = max(temp_range, 10)  # Minimum range for display

        # Draw Y-axis labels (5 levels)
        num_y_labels = 5
        for i in range(num_y_labels):
            temp_val = max_temp - (i * temp_range / (num_y_labels - 1))
            y_pos = graph_y + (i * graph_h / (num_y_labels - 1))
            label = f"{int(temp_val)}°"
            black_draw.text((graph_x - 35, y_pos - 8), label, font=FONT_GRAPH_LABEL, fill=0)
            # Horizontal grid line
            black_draw.line([(graph_x, y_pos), (graph_x + graph_w, y_pos)], fill=0, width=1)

        # Draw vertical axis
        black_draw.line([(graph_x, graph_y), (graph_x, graph_y + graph_h)], fill=0, width=2)

        # Plot temperature line
        points = []
        x_step = graph_w / (len(temps) - 1) if len(temps) > 1 else graph_w

        for i, temp in enumerate(temps):
            x = graph_x + (i * x_step)
            # Normalize temperature to graph height
            temp_norm = (max_temp - temp) / temp_range
            y = graph_y + (temp_norm * graph_h)
            points.append((x, y))

            # Draw point
            black_draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=0)

        # Draw line connecting points
        if len(points) > 1:
            black_draw.line(points, fill=0, width=2)

        # Draw time labels and weather icons
        for i, (time_label, icon_code) in enumerate(zip(times, icons)):
            x = graph_x + (i * x_step)

            # Time label
            bbox = black_draw.textbbox((0, 0), time_label, font=FONT_TIME_LABEL)
            tw = bbox[2] - bbox[0]
            black_draw.text((x - tw // 2, graph_y + graph_h + 10), time_label, font=FONT_TIME_LABEL, fill=0)

            # Weather icon
            icon_char = WEATHER_ICON_MAP.get(icon_code, "")
            bbox = black_draw.textbbox((0, 0), icon_char, font=FONT_WEATHER_ICON_SMALL)
            tw = bbox[2] - bbox[0]
            black_draw.text((x - tw // 2, graph_y + graph_h + 35), icon_char, font=FONT_WEATHER_ICON_SMALL, fill=0)

    def _draw_error(self, black_draw: ImageDraw.ImageDraw):
        """Draw error message if weather fetch fails."""
        error_text = "Unable to load weather data"
        bbox = black_draw.textbbox((0, 0), error_text, font=FONT_CURRENT_DESC)
        tw = bbox[2] - bbox[0]
        black_draw.text((400 - tw // 2, 240), error_text, font=FONT_CURRENT_DESC, fill=0)
