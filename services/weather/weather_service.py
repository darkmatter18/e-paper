from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CurrentWeather:
    """Current weather data."""

    temperature: float
    feels_like: float
    humidity: int
    description: str
    icon: str  # Weather icon code


@dataclass
class ForecastDay:
    """Daily forecast data."""

    date: str  # Date string (YYYY-MM-DD)
    temp_min: float
    temp_max: float
    description: str
    icon: str


@dataclass
class WeatherData:
    """Complete weather data with current and forecast."""

    current: CurrentWeather
    forecast: list[ForecastDay]


class WeatherService(ABC):
    """Abstract base class for weather services."""

    @abstractmethod
    def get_weather(self, lat: float, lon: float) -> WeatherData:
        """Fetch current weather and forecast for given coordinates."""
        pass
