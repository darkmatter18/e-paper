"""Application settings using Pydantic BaseSettings.

All configuration is managed through environment variables and this settings class.
Settings are loaded once and cached for the application lifetime.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DisplaySettings(BaseSettings):
    """E-paper display hardware settings.

    Hardware Constants (Fixed):
        WIDTH (800): Waveshare 7.5" B/V2 display width in pixels (read-only)
        HEIGHT (480): Waveshare 7.5" B/V2 display height in pixels (read-only)
    """

    # Hardware constants - Waveshare 7.5" B/V2 display specifications
    WIDTH: int = 800  # Fixed hardware specification
    HEIGHT: int = 480  # Fixed hardware specification

    full_refresh_interval: int = Field(
        default=15,
        ge=1,
        le=60,
        description="Minutes between full refreshes (activates red pigment)",
    )

    model_config = SettingsConfigDict(
        env_prefix="DISPLAY_",
        case_sensitive=False,
        extra="ignore",
    )


class WeatherSettings(BaseSettings):
    """Weather service API settings."""

    api_key: str = Field(
        default="",
        description="OpenWeatherMap API key (optional)",
    )
    latitude: float = Field(
        default=23.426022,
        description="Location latitude for weather data",
    )
    longitude: float = Field(
        default=87.550644,
        description="Location longitude for weather data",
    )
    units: Literal["metric", "imperial", "standard"] = Field(
        default="metric",
        description="Temperature units (metric=Celsius, imperial=Fahrenheit)",
    )

    model_config = SettingsConfigDict(
        env_prefix="WEATHER_",
        case_sensitive=False,
        extra="ignore",
    )


class TimezoneSettings(BaseSettings):
    """Timezone settings for display."""

    name: str = Field(
        default="IST",
        description="Timezone name",
    )
    utc_offset_hours: int = Field(
        default=5,
        ge=-12,
        le=14,
        description="Hours offset from UTC",
    )
    utc_offset_minutes: int = Field(
        default=30,
        ge=0,
        le=59,
        description="Minutes offset from UTC",
    )

    model_config = SettingsConfigDict(
        env_prefix="TIMEZONE_",
        case_sensitive=False,
        extra="ignore",
    )


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        case_sensitive=False,
        extra="ignore",
    )


class Settings(BaseSettings):
    """Main application settings.

    Aggregates all settings subsections and provides a single point of access
    for all configuration values. Settings are loaded from environment variables.

    Note:
        The .env file is loaded by load_dotenv() in main.py before any imports.
        Pydantic BaseSettings then reads from os.environ (populated by load_dotenv).

    Hardware Constants:
        DisplaySettings.WIDTH: Display width in pixels (800 - fixed)
        DisplaySettings.HEIGHT: Display height in pixels (480 - fixed)

    Environment Variables:
        DISPLAY_FULL_REFRESH_INTERVAL: Minutes between full refreshes (default: 15)
        WEATHER_API_KEY: OpenWeatherMap API key
        WEATHER_LATITUDE: Location latitude (default: 23.426022)
        WEATHER_LONGITUDE: Location longitude (default: 87.550644)
        WEATHER_UNITS: Temperature units - metric/imperial/standard (default: metric)
        TIMEZONE_NAME: Timezone name (default: IST)
        TIMEZONE_UTC_OFFSET_HOURS: Hours offset from UTC (default: 5)
        TIMEZONE_UTC_OFFSET_MINUTES: Minutes offset from UTC (default: 30)
        LOG_LEVEL: Logging level - DEBUG/INFO/WARNING/ERROR (default: INFO)
    """

    display: DisplaySettings = Field(default_factory=DisplaySettings)
    weather: WeatherSettings = Field(default_factory=WeatherSettings)
    timezone: TimezoneSettings = Field(default_factory=TimezoneSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="allow",  # Allow extra env vars for nested settings
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Settings are loaded once and cached for application lifetime.
    Uses LRU cache to ensure singleton behavior.

    Returns:
        Cached Settings instance with all configuration loaded.
    """
    return Settings()
