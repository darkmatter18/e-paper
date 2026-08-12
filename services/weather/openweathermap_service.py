import logging
from datetime import datetime

from services.weather.weather_service import (
    CurrentWeather,
    ForecastDay,
    WeatherData,
    WeatherService,
)
from utils import DateTimeUtil
from utils.http_client import HttpClient

logger = logging.getLogger(__name__)


class OpenWeatherMapService(WeatherService):
    """OpenWeatherMap API implementation of WeatherService."""

    BASE_URL = "https://api.openweathermap.org/data/2.5"

    def __init__(
        self, api_key: str, http_client: HttpClient | None = None, units: str = "metric"
    ):
        """
        Initialize OpenWeatherMap service.

        Args:
            api_key: OpenWeatherMap API key
            http_client: Optional HTTP client instance
            units: Temperature units ('metric', 'imperial', 'standard')
        """
        self.api_key = api_key
        self.http_client = http_client or HttpClient()
        self.units = units

    def get_weather(self, lat: float, lon: float) -> WeatherData:
        """Fetch current weather and forecast for given coordinates.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            WeatherData: Current weather and forecast

        Raises:
            Exception: If the API request fails
        """
        try:
            current = self._fetch_current(lat, lon)
            forecast = self._fetch_forecast(lat, lon)

            # Get today's rain probability from forecast
            if forecast:
                today = DateTimeUtil.now().strftime("%Y-%m-%d")
                for day in forecast:
                    if day.date == today:
                        current.rain_probability = day.rain_probability
                        break

            return WeatherData(current=current, forecast=forecast)

        except Exception as e:
            logger.error(f"Failed to fetch weather data: {e}")
            # Return fallback data
            return self._get_fallback_weather()

    def _fetch_current(self, lat: float, lon: float) -> CurrentWeather:
        """Fetch current weather data."""
        url = f"{self.BASE_URL}/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": self.units,
        }

        # Build query string manually
        query = "&".join(f"{k}={v}" for k, v in params.items())
        response = self.http_client.get(f"{url}?{query}")
        response.raise_for_status()

        data = response.json()

        return CurrentWeather(
            temperature=data["main"]["temp"],
            feels_like=data["main"]["feels_like"],
            humidity=data["main"]["humidity"],
            description=data["weather"][0]["description"],
            icon=data["weather"][0]["icon"],
        )

    def _fetch_forecast(self, lat: float, lon: float) -> list[ForecastDay]:
        """Fetch 5-day forecast data (returns next 5 days)."""
        url = f"{self.BASE_URL}/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": self.units,
        }

        query = "&".join(f"{k}={v}" for k, v in params.items())
        response = self.http_client.get(f"{url}?{query}")
        response.raise_for_status()

        data = response.json()

        # Group by date and get daily min/max
        daily_data = {}
        for item in data["list"]:
            dt = datetime.fromtimestamp(item["dt"])
            date_key = dt.strftime("%Y-%m-%d")

            if date_key not in daily_data:
                daily_data[date_key] = {
                    "temps": [],
                    "description": item["weather"][0]["description"],
                    "icon": item["weather"][0]["icon"],
                    "rain_probs": [],
                }

            daily_data[date_key]["temps"].append(item["main"]["temp"])
            # Rain probability from 'pop' (probability of precipitation)
            if "pop" in item:
                daily_data[date_key]["rain_probs"].append(int(item["pop"] * 100))

        # Convert to ForecastDay objects (take first 5 days)
        forecast = []
        for date_str in sorted(daily_data.keys())[:5]:
            day = daily_data[date_str]
            # Use max rain probability for the day
            rain_prob = max(day["rain_probs"]) if day["rain_probs"] else 0
            forecast.append(
                ForecastDay(
                    date=date_str,
                    temp_min=min(day["temps"]),
                    temp_max=max(day["temps"]),
                    description=day["description"],
                    icon=day["icon"],
                    rain_probability=rain_prob,
                )
            )

        return forecast

    def _get_fallback_weather(self) -> WeatherData:
        """Return fallback weather data when API fails."""
        return WeatherData(
            current=CurrentWeather(
                temperature=20.0,
                feels_like=20.0,
                humidity=50,
                description="unavailable",
                icon="01d",
            ),
            forecast=[
                ForecastDay(
                    date=DateTimeUtil.now().strftime("%Y-%m-%d"),
                    temp_min=15.0,
                    temp_max=25.0,
                    description="unavailable",
                    icon="01d",
                )
            ],
        )
