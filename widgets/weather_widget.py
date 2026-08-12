"""Weather widget - displays current weather and 5-day forecast."""
import os

from PIL import ImageDraw, ImageFont

from services.weather import WeatherService
from services.weather.openweathermap_service import OpenWeatherMapService
from widgets.widget import Widget, WidgetRegion

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Fonts
FONT_WEATHER_TEMP = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Righteous-Regular.ttf"), 28
)
FONT_WEATHER_DAY = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Righteous-Regular.ttf"), 18
)
FONT_WEATHER_SMALL = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Righteous-Regular.ttf"), 14
)
FONT_WEATHER_ICON = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "weathericons-regular-webfont.ttf"), 24
)

# OpenWeatherMap icon code to Weather Icons font character mapping
WEATHER_ICON_MAP = {
    "01d": "", "01n": "", "02d": "", "02n": "",
    "03d": "", "03n": "", "04d": "", "04n": "",
    "09d": "", "09n": "", "10d": "", "10n": "",
    "11d": "", "11n": "", "13d": "", "13n": "",
    "50d": "", "50n": "",
}


class WeatherWidget(Widget):
    """Displays weather in top-right area (400x240)."""

    def __init__(self):
        """Initialize weather widget with service and location.

        Args:
            weather_service: Weather service instance
            lat: Latitude
            lon: Longitude
        """
        super().__init__(WidgetRegion(x=400, y=0, width=400, height=240))
        api_key = os.getenv("OPENWEATHER_API_KEY", "")
        self.weather_service: WeatherService = OpenWeatherMapService(api_key)
        # Weather location

        self.lat = float(os.getenv("LATITUDE", "23.426022"))
        self.lon = float(os.getenv("LONGITUDE", "87.550644"))

    def draw(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None = None, **kwargs):
        """Draw weather information.

        Args:
            black_draw: PIL ImageDraw for black channel
            red_draw: Optional PIL ImageDraw for red channel
            **kwargs: Unused (weather data is fetched internally)
        """
        # Fetch weather data using internal service
        weather = self.weather_service.get_weather(self.lat, self.lon)

        qx, qy, qw = self.region.x, self.region.y, self.region.width
        current = weather.current
        forecast = weather.forecast[:5]

        # Current weather - single line layout
        y_line = qy + 25

        # Measure all elements first
        temp_text = f"{int(current.temperature)}°"
        temp_bbox = black_draw.textbbox((0, 0), temp_text, font=FONT_WEATHER_TEMP)
        temp_w = temp_bbox[2] - temp_bbox[0]
        temp_h = temp_bbox[3] - temp_bbox[1]

        desc_text = current.description.title()
        desc_bbox = black_draw.textbbox((0, 0), desc_text, font=FONT_WEATHER_DAY)
        desc_w = desc_bbox[2] - desc_bbox[0]

        # Rain percentage (if > 0)
        rain_text = ""
        rain_w = 0
        rain_h = 0
        if current.rain_probability > 0:
            rain_text = f"{current.rain_probability}%"
            rain_bbox = black_draw.textbbox((0, 0), rain_text, font=FONT_WEATHER_SMALL)
            rain_w = rain_bbox[2] - rain_bbox[0]
            rain_h = rain_bbox[3] - rain_bbox[1]

        # Weather icon
        icon_char = WEATHER_ICON_MAP.get(current.icon, "")
        icon_bbox = black_draw.textbbox((0, 0), icon_char, font=FONT_WEATHER_ICON)
        icon_w = icon_bbox[2] - icon_bbox[0]
        icon_h = icon_bbox[3] - icon_bbox[1]

        # Calculate total width and center everything
        spacing = 15
        total_w = temp_w + spacing + desc_w
        if current.rain_probability > 0:
            total_w += spacing + rain_w
        total_w += spacing + icon_w

        start_x = qx + (qw - total_w) // 2
        x_pos = start_x

        # Draw temperature in RED if red_draw provided
        temp_target = red_draw if red_draw else black_draw
        temp_target.text((x_pos, y_line - temp_h + 4), temp_text, font=FONT_WEATHER_TEMP, fill=0)
        x_pos += temp_w + spacing

        # Draw description
        black_draw.text((x_pos, y_line - 6), desc_text, font=FONT_WEATHER_DAY, fill=0)
        x_pos += desc_w + spacing

        # Draw rain percentage if > 0
        if current.rain_probability > 0:
            black_draw.text((x_pos, y_line - rain_h + 6), rain_text, font=FONT_WEATHER_SMALL, fill=0)
            x_pos += rain_w + spacing

        # Draw weather icon
        icon_y = y_line - 4
        black_draw.text((x_pos, icon_y - icon_h // 2), icon_char, font=FONT_WEATHER_ICON, fill=0)

        # Horizontal separator line
        black_draw.line([qx + 20, qy + 55, qx + qw - 20, qy + 55], fill=0, width=2)

        # 5-day forecast bars
        if forecast:
            self._draw_forecast(black_draw, red_draw, forecast, qx, qy, qw)

    def _draw_forecast(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None,
                      forecast: list, qx: int, qy: int, qw: int):
        """Draw 5-day forecast with bars and icons."""
        from datetime import datetime

        bar_w = 24  # Fixed narrow width
        margin = 30
        available_width = qw - 2 * margin
        total_bar_width = len(forecast) * bar_w
        total_gap_width = available_width - total_bar_width
        bar_spacing = total_gap_width // (len(forecast) + 1)
        start_x = qx + margin + bar_spacing

        bar_y = qy + 95
        bar_h_max = 50

        # Find temp range
        all_temps = [day.temp_min for day in forecast] + [day.temp_max for day in forecast]
        temp_range = max(all_temps) - min(all_temps)
        temp_range = max(temp_range, 10)  # Minimum 10° range

        for i, day in enumerate(forecast):
            center_x = start_x + i * (bar_w + bar_spacing) + bar_w // 2

            # Weather icon above bar
            icon_char = WEATHER_ICON_MAP.get(day.icon, "")
            icon_bbox = black_draw.textbbox((0, 0), icon_char, font=FONT_WEATHER_ICON)
            icon_w = icon_bbox[2] - icon_bbox[0]
            black_draw.text((center_x - icon_w // 2, bar_y - 30), icon_char, font=FONT_WEATHER_ICON, fill=0)

            # Max temp label above bar (in RED if red_draw provided)
            max_temp = f"{int(day.temp_max)}°"
            bbox = black_draw.textbbox((0, 0), max_temp, font=FONT_WEATHER_SMALL)
            tw = bbox[2] - bbox[0]
            max_target = red_draw if red_draw else black_draw
            max_target.text((center_x - tw // 2, bar_y - 16), max_temp, font=FONT_WEATHER_SMALL, fill=0)

            # Temperature bar (scaled to temp range)
            bar_h = int(((day.temp_max - day.temp_min) / temp_range) * bar_h_max)
            bar_h = max(bar_h, 10)  # Minimum bar height
            bar_top = bar_y
            bar_bot = bar_top + bar_h

            bar_x1 = start_x + i * (bar_w + bar_spacing)
            bar_x2 = bar_x1 + bar_w
            black_draw.rectangle([bar_x1, bar_top, bar_x2, bar_bot], outline=0, width=2)

            # Min temp below bar (fixed position)
            min_temp = f"{int(day.temp_min)}°"
            bbox = black_draw.textbbox((0, 0), min_temp, font=FONT_WEATHER_SMALL)
            tw = bbox[2] - bbox[0]
            min_y = bar_y + bar_h_max + 2
            black_draw.text((center_x - tw // 2, min_y), min_temp, font=FONT_WEATHER_SMALL, fill=0)

            # Rain percentage below min temp (if > 0)
            if day.rain_probability > 0:
                rain_text = f"{day.rain_probability}%"
                bbox = black_draw.textbbox((0, 0), rain_text, font=FONT_WEATHER_SMALL)
                tw = bbox[2] - bbox[0]
                black_draw.text((center_x - tw // 2, min_y + 16), rain_text, font=FONT_WEATHER_SMALL, fill=0)

            # Day label at bottom
            dt = datetime.strptime(day.date, "%Y-%m-%d")  # noqa: DTZ007
            day_label = dt.strftime("%a").upper()
            bbox = black_draw.textbbox((0, 0), day_label, font=FONT_WEATHER_SMALL)
            tw = bbox[2] - bbox[0]
            day_y = min_y + (32 if day.rain_probability > 0 else 16)
            black_draw.text((center_x - tw // 2, day_y), day_label, font=FONT_WEATHER_SMALL, fill=0)

    def draw_decorations(self, black_draw: ImageDraw.ImageDraw):
        """Draw black decorative elements."""
        qx, qy, qw = self.region.x, self.region.y, self.region.width

        # Corner brackets for weather section
        for cx, cy, sx, sy in [
            (qx + 15, qy + 15, 1, 1),
            (qx + qw - 15, qy + 15, -1, 1),
        ]:
            black_draw.line([cx, cy, cx + sx * 20, cy], fill=0, width=2)
            black_draw.line([cx, cy, cx, cy + sy * 20], fill=0, width=2)

    def draw_red_decorations(self, red_draw: ImageDraw.ImageDraw):
        """Draw red decorative elements."""
        qx, qy = self.region.x, self.region.y

        # Red corner dots
        for cx, cy in [(qx + 25, qy + 10), (qx + 375, qy + 10)]:
            red_draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=0)
