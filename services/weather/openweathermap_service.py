"""OpenWeatherMap API integration for weather data and forecasts.

This module implements the WeatherService interface using the OpenWeatherMap API
(https://openweathermap.org). It provides production-ready weather fetching with
support for current conditions and 5-day forecasts.

Key Features:
    - Current weather conditions (temperature, humidity, description)
    - 5-day forecast aggregated by day (min/max temps, rain probability)
    - Configurable temperature units (metric, imperial, standard)
    - Rain probability extraction from forecast data
    - Automatic fallback data on API failures
    - HTTP client abstraction for testing

API Integration:
    - Base URL: https://api.openweathermap.org/data/2.5
    - Endpoints:
        - /weather: Current weather conditions
        - /forecast: 5-day forecast in 3-hour intervals
    - Authentication: API key via 'appid' query parameter
    - Rate Limits: Free tier = 60 calls/minute, 1,000,000 calls/month
    - Response Format: JSON

Temperature Units:
    - 'metric': Celsius (°C) - default
    - 'imperial': Fahrenheit (°F)
    - 'standard': Kelvin (K)

Data Aggregation:
    The /forecast endpoint returns 3-hour interval forecasts. This service
    aggregates them into daily summaries:
    - Groups forecast entries by date (local date from timestamp)
    - Calculates daily min/max from all intervals for that date
    - Uses maximum rain probability across all intervals
    - Takes first occurrence's description and icon as representative

Error Handling:
    All network and API errors are caught and logged. The service returns
    fallback weather data with safe defaults (20°C, 50% humidity, "unavailable"
    description) on any failure.

Caching Strategy:
    This service does NOT implement caching internally. For production use,
    consider wrapping it with a caching layer or calling it less frequently:
    - Recommended: Cache at application level for 10-30 minutes
    - Weather data changes slowly, frequent calls waste API quota
    - Round coordinates to ~0.01° precision to improve cache hit rate

API Response Examples:
    Current weather (/weather):
        {
            "main": {
                "temp": 32.5,
                "feels_like": 35.2,
                "humidity": 65
            },
            "weather": [
                {"description": "scattered clouds", "icon": "03d"}
            ]
        }

    Forecast (/forecast):
        {
            "list": [
                {
                    "dt": 1723804800,
                    "main": {"temp": 30.2},
                    "weather": [{"description": "clear sky", "icon": "01d"}],
                    "pop": 0.15  // Probability of precipitation (0.0-1.0)
                },
                ...
            ]
        }

See Also:
    - WeatherService: Abstract base class
    - OpenWeatherMap API docs: https://openweathermap.org/api
    - display_clock.py: Integration into e-paper display
"""

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
    """Production weather service implementation using OpenWeatherMap API.

    This class fetches weather data from OpenWeatherMap's Current Weather Data
    and 5-day Forecast APIs. It handles data transformation, aggregation, and
    error recovery internally.

    The service makes two API calls per weather request:
    1. /weather endpoint for current conditions
    2. /forecast endpoint for 5-day predictions

    Forecast data comes in 3-hour intervals and is aggregated into daily
    summaries with min/max temperatures and maximum rain probability.

    Attributes:
        BASE_URL (str): Class constant for OpenWeatherMap API base URL.
            All endpoints are relative to this URL.
        api_key (str): OpenWeatherMap API key for authentication. Get yours
            at https://home.openweathermap.org/api_keys
        http_client (HttpClient): HTTP client instance for making requests.
            Injected for testability and timeout configuration.
        units (str): Temperature unit system for API responses.
            - 'metric': Celsius (default)
            - 'imperial': Fahrenheit
            - 'standard': Kelvin

    Note:
        API key must be activated before use. New keys may take up to 2 hours
        to become active. Test at https://openweathermap.org/api/one-call-3
    """

    BASE_URL = "https://api.openweathermap.org/data/2.5"

    def __init__(
        self, api_key: str, http_client: HttpClient | None = None, units: str = "metric"
    ):
        """Initialize OpenWeatherMap service with API credentials and options.

        Args:
            api_key (str): OpenWeatherMap API key for authentication. Required.
                Obtain from https://home.openweathermap.org/api_keys. The key
                must be activated (may take up to 2 hours for new keys).
            http_client (HttpClient | None, optional): HTTP client instance to use
                for API requests. If None, creates a new HttpClient() with default
                settings. Providing a custom client is useful for configuring
                timeouts or for testing. Defaults to None.
            units (str, optional): Temperature unit system for API responses.
                Valid values are:
                - 'metric': Celsius (°C), meters/sec for wind
                - 'imperial': Fahrenheit (°F), miles/hour for wind
                - 'standard': Kelvin (K), meters/sec for wind
                Defaults to 'metric'.

        Note:
            The units parameter is passed to OpenWeatherMap API, not used for
            local conversion. API returns data in the requested units.
        """
        logger.info(f"Initializing API Key={api_key}, Units={units}")
        self.api_key = api_key
        self.http_client = http_client or HttpClient()
        self.units = units

    def get_weather(self, lat: float, lon: float) -> WeatherData:
        """Fetch current weather and forecast for specified coordinates.

        Makes two API calls to OpenWeatherMap:
        1. Current weather endpoint for real-time conditions
        2. 5-day forecast endpoint for daily predictions

        The forecast data is aggregated from 3-hour intervals into daily
        summaries. Today's rain probability from the forecast is also
        backfilled into the current weather data.

        Args:
            lat (float): Latitude in decimal degrees (-90 to 90).
                Positive is North, negative is South.
            lon (float): Longitude in decimal degrees (-180 to 180).
                Positive is East, negative is West.

        Returns:
            WeatherData: Complete weather information with current conditions
                and up to 5 days of forecast. On any error, returns fallback
                data with sensible defaults (20°C, "unavailable" description).

        Note:
            Makes 2 API calls per invocation. Consider caching results
            for 10-30 minutes to stay within rate limits and reduce latency.
            Free tier allows 60 calls/minute = 30 weather requests/minute.
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
        """Fetch current weather conditions from OpenWeatherMap API.

        Calls the /weather endpoint to get real-time weather data including
        temperature, feels-like temperature, humidity, and conditions.

        Args:
            lat (float): Latitude in decimal degrees.
            lon (float): Longitude in decimal degrees.

        Returns:
            CurrentWeather: Current weather conditions with rain_probability
                set to 0 (will be updated from forecast data by caller).

        Raises:
            Exception: On network errors, HTTP errors, or invalid JSON response.
                Caller (get_weather) catches these and returns fallback data.

        API Response Structure:
            {
                "main": {
                    "temp": 32.5,
                    "feels_like": 35.2,
                    "humidity": 65
                },
                "weather": [
                    {
                        "description": "scattered clouds",
                        "icon": "03d"
                    }
                ]
            }

        Note:
            Query parameters are manually formatted to avoid issues with
            requests library's default parameter encoding.
        """
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
        """Fetch 5-day forecast and aggregate into daily summaries.

        Calls the /forecast endpoint which returns 3-hour interval forecasts
        for 5 days (40 data points). Groups intervals by date and calculates:
        - Daily min/max temperatures (from all intervals for that date)
        - Maximum rain probability across all intervals
        - Representative description and icon (from first interval of day)

        Args:
            lat (float): Latitude in decimal degrees.
            lon (float): Longitude in decimal degrees.

        Returns:
            list[ForecastDay]: List of up to 5 ForecastDay objects, ordered
                chronologically. May return fewer than 5 days if API data
                is incomplete.

        Raises:
            Exception: On network errors, HTTP errors, or invalid JSON response.
                Caller (get_weather) catches these and returns fallback data.

        API Response Structure:
            {
                "list": [
                    {
                        "dt": 1723804800,  // Unix timestamp
                        "main": {"temp": 30.2},
                        "weather": [{"description": "clear sky", "icon": "01d"}],
                        "pop": 0.15  // Probability of precipitation (0.0-1.0)
                    },
                    // ... 39 more 3-hour intervals
                ]
            }

        Aggregation Logic:
            For each unique date (derived from timestamp):
            1. Collect all temperature values from intervals on that date
            2. Collect all rain probabilities ("pop" field)
            3. Use first occurrence's description and icon as representative
            4. Calculate daily min = min(all temps), max = max(all temps)
            5. Use max rain probability for the day

        Note:
            Uses naive datetime.fromtimestamp() which converts to system local
            time. This is intentional - we want forecasts grouped by local date,
            not UTC date.
        """
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
        """Generate fallback weather data for error cases.

        Returns safe default weather data when API calls fail due to network
        errors, authentication issues, or invalid responses. The fallback
        uses neutral values that won't cause display issues.

        Returns:
            WeatherData: Fallback weather with:
                - Temperature: 20°C (comfortable room temperature)
                - Feels like: 20°C (same as actual)
                - Humidity: 50% (moderate)
                - Description: "unavailable" (clear error indicator)
                - Icon: "01d" (clear sky icon, safe default)
                - Forecast: Single day with 15-25°C range

        Note:
            Uses current date from DateTimeUtil.now() for the forecast date
            to ensure consistency with the rest of the application's
            timezone handling.
        """
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
