"""Weather widget - displays current weather and 5-day forecast.

This module implements a weather information widget showing current conditions
and a 5-day forecast visualization. Designed for the top-right area (400x240)
of the 800x480 e-paper display.

Features:
    - Current weather: Temperature (red), description, rain %, weather icon
    - 5-day forecast: Bar chart showing temp range with icons and details
    - Data fetched from OpenWeatherMap API via internal service
    - Weather Icons font for consistent meteorological symbols

Layout:
    - Top section (y=0-55): Current weather in single-line layout
    - Separator line (y=55): Horizontal divider
    - Forecast section (y=95-240): Five vertical bars with annotations

Configuration:
    Uses Pydantic settings from settings.weather:
    - api_key: API key for OpenWeatherMap service (WEATHER_API_KEY)
    - latitude: Location latitude (WEATHER_LATITUDE, default: 23.426022)
    - longitude: Location longitude (WEATHER_LONGITUDE, default: 87.550644)

Weather Icons Font:
    Uses Weather Icons webfont (weathericons-regular-webfont.ttf) with Unicode
    private use area characters. The WEATHER_ICON_MAP translates OpenWeatherMap
    icon codes (e.g., "01d" for clear day) to font characters.

Color Usage:
    - Black: All text except temperature, icons, bars, decorations
    - Red: Current temperature, max temperature labels (emphasis)
"""
from PIL import ImageDraw, ImageFont

from services.weather import WeatherService
from services.weather.openweathermap_service import OpenWeatherMapService
from settings import get_settings
from settings.fonts import FONT_RIGHTEOUS, FONT_WEATHER_ICONS
from widgets.base import Widget, WidgetRegion

# Weather display fonts
FONT_WEATHER_TEMP = ImageFont.truetype(str(FONT_RIGHTEOUS), 28)  # Current temperature
FONT_WEATHER_DAY = ImageFont.truetype(str(FONT_RIGHTEOUS), 18)  # Weather description
FONT_WEATHER_SMALL = ImageFont.truetype(str(FONT_RIGHTEOUS), 14)  # Forecast details
FONT_WEATHER_ICON = ImageFont.truetype(str(FONT_WEATHER_ICONS), 24)  # Weather icons

# OpenWeatherMap icon code to Weather Icons font character mapping
# Maps OWM 3-character codes (condition + day/night) to Unicode private use characters
WEATHER_ICON_MAP = {
    "01d": "", "01n": "",  # Clear sky (sun/moon)
    "02d": "", "02n": "",  # Few clouds (partly cloudy)
    "03d": "", "03n": "",  # Scattered clouds
    "04d": "", "04n": "",  # Broken clouds
    "09d": "", "09n": "",  # Shower rain
    "10d": "", "10n": "",  # Rain
    "11d": "", "11n": "",  # Thunderstorm
    "13d": "", "13n": "",  # Snow
    "50d": "", "50n": "",  # Mist/fog
}


class WeatherWidget(Widget):
    """Displays weather in top-right area (400x240).

    Shows current weather conditions and a 5-day forecast with visual bar chart.
    Weather data is fetched on-demand from OpenWeatherMap API during each full refresh.

    Layout Strategy:
        - Current weather: Single-line horizontal layout with all elements centered
        - Forecast: Five evenly-spaced vertical bars with annotations above/below
        - Temperature bars scaled to relative temperature range for visual comparison

    Data Flow:
        Widget owns a WeatherService instance and fetches data internally during
        draw(). This keeps the widget self-contained and allows it to handle errors
        and caching transparently.

    Attributes:
        region: WidgetRegion(x=400, y=0, width=400, height=240) - top-right area
        weather_service: OpenWeatherMapService instance for fetching weather data
        lat: Location latitude from settings.weather.latitude
        lon: Location longitude from settings.weather.longitude
    """

    def __init__(self, region: WidgetRegion | None = None):
        """Initialize weather widget with service and location.

        Args:
            region: Widget display region (defaults to upper-right quadrant)

        Reads configuration from Pydantic settings (settings.weather):
        - api_key: Required for API access (WEATHER_API_KEY env var)
        - latitude: Location latitude (WEATHER_LATITUDE env var, default: 23.426022)
        - longitude: Location longitude (WEATHER_LONGITUDE env var, default: 87.550644)

        Raises:
            KeyError: If WEATHER_API_KEY is not set (handled by service layer).
        """
        if region is None:
            region = WidgetRegion(x=400, y=0, width=400, height=240)
        super().__init__(region)
        settings = get_settings()
        self.weather_service: WeatherService = OpenWeatherMapService(settings.weather.api_key)

        # Weather location from settings (defaults to coordinates in West Bengal, India)
        self.lat = settings.weather.latitude
        self.lon = settings.weather.longitude

    def draw(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None = None, **kwargs):
        """Draw weather information with current conditions and forecast.

        Fetches weather data internally and renders:
        1. Current weather line: Temp (red) + description + rain % + icon
        2. Horizontal separator
        3. 5-day forecast bars with icons, temps, rain %, and day labels

        Args:
            black_draw: PIL ImageDraw context for black channel. Used for all text
                except temperatures, plus icons, bars, and decorations.
            red_draw: Optional PIL ImageDraw context for red channel. When provided,
                current temperature and forecast max temps are drawn in red.
            **kwargs: Unused. Weather data is fetched via self.weather_service.

        Layout Details:
            Current weather (y=25): All elements centered as a single line
            - Temperature (28pt, red/black)
            - Description (18pt, title case)
            - Rain percentage (14pt, if > 0)
            - Weather icon (24pt Weather Icons font)

            Forecast (y=95-240): Five bars with 24px width, evenly spaced
            - Icon above bar
            - Max temp above bar (red/black, 14pt)
            - Temperature bar (scaled to range)
            - Min temp below bar (14pt)
            - Rain percentage below min temp (14pt, if > 0)
            - Day label at bottom (14pt, 3-letter abbreviation)

        Note:
            Forecast bar heights are scaled relative to the temperature range across
            all 5 days, providing visual comparison of relative temperature swings.
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
        """Draw 5-day forecast with temperature bars and annotations.

        Renders five vertical bars representing temperature ranges, with comprehensive
        annotations: weather icon, max/min temps, rain probability, and day labels.
        Bar heights are scaled relative to the temperature range for visual comparison.

        Args:
            black_draw: PIL ImageDraw context for black channel.
            red_draw: Optional PIL ImageDraw context for red channel. When provided,
                max temperature labels are drawn in red.
            forecast: List of ForecastDay objects (length 5). Each contains:
                - date: YYYY-MM-DD format
                - temp_min, temp_max: Temperature range in degrees
                - rain_probability: Integer percentage (0-100)
                - icon: OpenWeatherMap icon code (e.g., "01d")
            qx: Region X offset (typically 400).
            qy: Region Y offset (typically 0).
            qw: Region width (typically 400).

        Layout Per Bar:
            - Icon: y=bar_y-30 (weather symbol, 24pt)
            - Max temp: y=bar_y-16 (red/black, 14pt)
            - Bar: y=bar_y to bar_y+bar_h (scaled height, 2px outline)
            - Min temp: y=bar_y+bar_h_max+2 (fixed position, 14pt)
            - Rain %: y=min_y+16 (if > 0, 14pt)
            - Day: y=min_y+32 or +16 (3-letter abbreviation, 14pt)

        Spacing Algorithm:
            Available width is divided into (n+1) gaps plus n bars:
            - Margin: 30px on each side
            - Bar width: 24px (fixed)
            - Gaps: (available_width - total_bar_width) / (n + 1)
            - This ensures even spacing with equal margins on both sides

        Temperature Scaling:
            Bar heights are proportional to (temp_max - temp_min) / total_range,
            capped at bar_h_max=50px. Minimum bar height is 10px for visibility.

        Note:
            All elements are horizontally centered on their bar's center_x coordinate.
        """
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
        """Draw black decorative elements around weather widget.

        Adds minimal corner brackets at top-left and top-right to frame the
        weather section without overwhelming the information-dense content.

        Args:
            black_draw: PIL ImageDraw context for black channel.

        Note:
            Weather widget uses minimal decoration compared to other widgets since
            it contains more functional data (current + 5-day forecast). Corner
            brackets provide framing without cluttering the forecast visualization.
            Called only during full refresh.
        """
        qx, qy, qw = self.region.x, self.region.y, self.region.width

        # Corner brackets for weather section
        for cx, cy, sx, sy in [
            (qx + 15, qy + 15, 1, 1),
            (qx + qw - 15, qy + 15, -1, 1),
        ]:
            black_draw.line([cx, cy, cx + sx * 20, cy], fill=0, width=2)
            black_draw.line([cx, cy, cx, cy + sy * 20], fill=0, width=2)

    def draw_red_decorations(self, red_draw: ImageDraw.ImageDraw):
        """Draw red decorative accent elements.

        Adds subtle red dots at top corners to balance the widget's appearance
        and coordinate with red temperature text.

        Args:
            red_draw: PIL ImageDraw context for red channel.

        Note:
            Minimal red decoration to avoid competing with functional red elements
            (current temp, max temps in forecast). Called only during full refresh.
        """
        qx, qy = self.region.x, self.region.y

        # Red corner dots
        for cx, cy in [(qx + 25, qy + 10), (qx + 375, qy + 10)]:
            red_draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=0)
