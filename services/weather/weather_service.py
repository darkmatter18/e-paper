"""Abstract base classes and data models for weather services.

This module defines the contract for weather service implementations used in the
e-paper clock application. It provides a unified abstraction layer that allows
different weather providers (OpenWeatherMap, Weather.gov, custom APIs) to be
used interchangeably.

Key Components:
    - CurrentWeather: Real-time weather conditions at a location
    - ForecastDay: Daily weather forecast data
    - WeatherData: Container combining current weather and multi-day forecast
    - WeatherService: Abstract base class defining the weather service interface

Data Models:
    The weather data models use simple, flat structures optimized for display
    on the e-paper screen:
    - Temperatures in service-configured units (typically Celsius/Fahrenheit)
    - Weather icon codes for mapping to display symbols
    - Rain probability as integer percentage (0-100)
    - Dates as ISO 8601 strings (YYYY-MM-DD) for consistency

Architecture Notes:
    The abstract base class pattern allows the display code to depend on the
    interface rather than specific implementations. This enables:
    - Easy switching between weather providers
    - Provider-specific caching and rate limiting strategies
    - Mock implementations for testing and development
    - Fallback data when API is unavailable
    - Multiple weather sources (primary + backup)

Service implementations should handle:
    - API authentication and key management
    - Unit conversion (metric/imperial)
    - Caching to reduce API calls (recommended: 10-30 min cache)
    - Error handling with sensible fallback data
    - Rate limiting per API provider's terms
    - Coordinate validation and bounds checking

See Also:
    - OpenWeatherMapService: Production implementation using OpenWeatherMap API
    - display_clock.py: Integration into the e-paper display system
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CurrentWeather:
    """Real-time weather conditions at a specific location.

    Represents the current weather state with all data needed for display
    on the e-paper clock. Temperature values are in the units specified
    by the service configuration (typically Celsius or Fahrenheit).

    Attributes:
        temperature (float): Current temperature at the location. Units depend
            on service configuration (typically °C or °F).
        feels_like (float): "Feels like" or apparent temperature accounting for
            wind chill or heat index. Same units as temperature.
        humidity (int): Relative humidity as percentage (0-100). Integer value
            for display simplicity.
        description (str): Human-readable weather description from the provider.
            Examples: "clear sky", "light rain", "partly cloudy". Used for
            display text, should be lowercase for consistency.
        icon (str): Weather icon code from the provider's icon set. Used to
            map to display symbols or images. Format varies by provider
            (e.g., OpenWeatherMap uses "01d", "10n", etc.).
        rain_probability (int, optional): Probability of precipitation as
            percentage (0-100). Defaults to 0. Some providers include this
            in current weather, others only in forecast.

    Note:
        Icon codes are provider-specific. The display layer should map these
        to appropriate symbols or images based on the provider in use.
    """

    temperature: float
    feels_like: float
    humidity: int
    description: str
    icon: str  # Weather icon code
    rain_probability: int = 0  # Rain probability percentage (0-100)


@dataclass
class ForecastDay:
    """Daily weather forecast data for a single day.

    Represents a day's weather forecast with min/max temperatures and
    representative conditions. Used for multi-day forecast displays.

    Attributes:
        date (str): Date of forecast in ISO 8601 format (YYYY-MM-DD).
            String format for consistency and easy comparison. Should be
            in the location's local date, not UTC.
        temp_min (float): Minimum temperature expected for the day.
            Units match service configuration (typically °C or °F).
        temp_max (float): Maximum temperature expected for the day.
            Same units as temp_min.
        description (str): Representative weather description for the day.
            Often the most significant condition or midday weather.
            Should be lowercase for consistency.
        icon (str): Weather icon code representing the day's conditions.
            Provider-specific format, typically the most representative
            icon for the day (often from midday forecast).
        rain_probability (int, optional): Maximum probability of precipitation
            during the day as percentage (0-100). Defaults to 0. Usually the
            peak rain chance across all forecast periods for that day.

    Note:
        Providers typically return 3-hour or 6-hour interval forecasts.
        Implementations should aggregate these into daily summaries with
        min/max temperatures and the most representative conditions.
    """

    date: str  # Date string (YYYY-MM-DD)
    temp_min: float
    temp_max: float
    description: str
    icon: str
    rain_probability: int = 0  # Rain probability percentage (0-100)


@dataclass
class WeatherData:
    """Complete weather information combining current conditions and forecast.

    Container class that packages current weather with multi-day forecast.
    This is the top-level data structure returned by WeatherService
    implementations.

    Attributes:
        current (CurrentWeather): Current real-time weather conditions.
            Contains temperature, humidity, description, and other
            immediate weather information.
        forecast (list[ForecastDay]): List of daily forecasts ordered
            chronologically. Typically includes today plus 4-7 future days
            depending on the provider. Empty list is valid if forecast is
            unavailable.

    Note:
        Some providers include "today" in the forecast list, others don't.
        Implementations should document their behavior. The forecast list
        order should always be chronological (earliest to latest).
    """

    current: CurrentWeather
    forecast: list[ForecastDay]


class WeatherService(ABC):
    """Abstract base class defining the contract for weather service implementations.

    This abstract class establishes the interface that all weather services must
    implement. Subclasses handle provider-specific API communication, data
    transformation, caching, and error handling.

    The interface is intentionally minimal and location-based to support different
    weather providers:
    - Public APIs (OpenWeatherMap, Weather.gov, WeatherAPI)
    - Private/commercial weather services
    - Mock implementations for testing
    - Cached/offline data sources

    Implementing Classes:
        Implementations should provide:
        - API authentication and key management
        - Geographic coordinate validation
        - Unit conversion to consistent system
        - Caching strategy (10-30 min recommended for weather)
        - Error handling with fallback data
        - Rate limiting per provider's terms
        - Logging for debugging

    Caching Strategy:
        Weather data changes slowly. Recommended caching:
        - Current weather: 10-15 minutes
        - Forecast: 30-60 minutes
        - Cache by location (lat/lon rounded to ~1km precision)
        - Invalidate on cache age or midnight boundary

    Error Handling:
        Implementations should NOT raise exceptions for normal error cases
        (network failures, API errors). Instead, they should:
        - Log the error with appropriate severity
        - Return fallback WeatherData with sensible defaults
        - Cache fallback to prevent retry storms
        - Only raise on programmer errors (invalid arguments, etc.)

    See Also:
        - OpenWeatherMapService: Production implementation
        - CurrentWeather, ForecastDay, WeatherData: Data models
        - display_clock.py: Integration into display system
    """

    @abstractmethod
    def get_weather(self, lat: float, lon: float) -> WeatherData:
        """Fetch current weather and forecast for specified coordinates.

        Retrieves complete weather information (current conditions + forecast)
        for a geographic location. Implementations should cache results and
        handle errors internally.

        Args:
            lat (float): Latitude of the location in decimal degrees.
                Valid range: -90.0 to 90.0. Positive values are North,
                negative are South.
            lon (float): Longitude of the location in decimal degrees.
                Valid range: -180.0 to 180.0. Positive values are East,
                negative are West.

        Returns:
            WeatherData: Complete weather information with current conditions
                and forecast list. Never returns None. On error, should return
                fallback data with reasonable defaults.

        Raises:
            NotImplementedError: If called on abstract base class directly.
            ValueError: (optional) If coordinates are invalid (out of range).

        Implementation Guidelines:
            - Validate coordinate ranges (lat: -90 to 90, lon: -180 to 180)
            - Round coordinates to reduce cache key space (~0.01° = ~1km)
            - Cache results for 10-30 minutes to reduce API calls
            - Handle all network/API errors internally (don't propagate)
            - Log errors with enough context for debugging
            - Return fallback WeatherData on any failure
            - Include timestamp in logs for cache debugging

        Note:
            Some providers charge per API call. Aggressive caching (15-30 min)
            is recommended. Round coordinates to limit cache key space.
        """
