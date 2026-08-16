# Settings Management Guide

## Overview

The application now uses **Pydantic Settings** for configuration management. All configuration is centralized in the `settings/` directory with type-safe, validated settings loaded from environment variables.

## Structure

```
settings/
├── __init__.py       # Package exports
└── settings.py       # Pydantic settings classes
```

## Settings Classes

### 1. DisplaySettings
E-paper display hardware configuration:
- `width`: Display width in pixels (default: 800)
- `height`: Display height in pixels (default: 480)
- `full_refresh_interval`: Minutes between full refreshes (default: 15, range: 1-60)

### 2. WeatherSettings
Weather service API configuration:
- `api_key`: OpenWeatherMap API key (optional)
- `latitude`: Location latitude (default: 23.426022)
- `longitude`: Location longitude (default: 87.550644)
- `units`: Temperature units - metric/imperial/standard (default: metric)

### 3. LoggingSettings
Application logging configuration:
- `level`: Log level - DEBUG/INFO/WARNING/ERROR/CRITICAL (default: INFO)
- `format`: Log message format string

### 4. TimezoneSettings
Timezone configuration:
- `name`: Timezone name (default: IST)
- `utc_offset_hours`: Hours offset from UTC (default: 5, range: -12 to 14)
- `utc_offset_minutes`: Minutes offset from UTC (default: 30, range: 0-59)

### 5. Settings (Main)
Aggregates all subsettings into one unified configuration object.

## Environment Variables

All settings can be configured via environment variables with prefixes:

```bash
# Display settings (prefix: DISPLAY_)
DISPLAY_WIDTH=800
DISPLAY_HEIGHT=480
DISPLAY_FULL_REFRESH_INTERVAL=15

# Weather settings (prefix: WEATHER_)
WEATHER_API_KEY=your_api_key_here
WEATHER_LATITUDE=23.426022
WEATHER_LONGITUDE=87.550644
WEATHER_UNITS=metric

# Logging settings (prefix: LOG_)
LOG_LEVEL=INFO
LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Timezone settings (prefix: TIMEZONE_)
TIMEZONE_NAME=IST
TIMEZONE_UTC_OFFSET_HOURS=5
TIMEZONE_UTC_OFFSET_MINUTES=30
```

## Usage

### Getting Settings

```python
from settings import get_settings

# Get cached settings instance (singleton)
settings = get_settings()

# Access nested settings
print(settings.display.width)  # 800
print(settings.weather.latitude)  # 23.426022
print(settings.logging.level)  # INFO
print(settings.timezone.name)  # IST
```

### In Application Code

Settings are automatically loaded and cached:

```python
# engine.py
from settings import get_settings

settings = get_settings()

class Engine:
    def __init__(self, screen: Screen):
        self.display_width = settings.display.width
        self.full_refresh_interval = settings.display.full_refresh_interval
```

### Validation

Pydantic automatically validates all settings:
- Type checking (int, float, str, Literal)
- Range validation (ge, le constraints)
- Required vs optional fields
- Enum validation for literal types

```python
# This would raise ValidationError:
DISPLAY_FULL_REFRESH_INTERVAL=100  # Error: value must be <= 60
WEATHER_UNITS=fahrenheit  # Error: must be metric/imperial/standard
```

## Benefits

✅ **Type Safety**: Full type hints with Pydantic validation  
✅ **Centralized**: All configuration in one place  
✅ **Validated**: Automatic validation of values and types  
✅ **Environment-Based**: Easy configuration via .env files  
✅ **Cached**: Settings loaded once via @lru_cache  
✅ **IDE Support**: Full autocomplete and type checking  
✅ **Documented**: Inline descriptions for all fields  

## Migration from Old Code

### Before (hardcoded)
```python
DISPLAY_W = 800
DISPLAY_H = 480
FULL_REFRESH_MIN = 15

lat = float(os.getenv("LATITUDE", "23.426022"))
lon = float(os.getenv("LONGITUDE", "87.550644"))
```

### After (Pydantic settings)
```python
from settings import get_settings

settings = get_settings()

width = settings.display.width
height = settings.display.height
refresh_interval = settings.display.full_refresh_interval

lat = settings.weather.latitude
lon = settings.weather.longitude
```

## Files Updated

1. **settings/settings.py** - New Pydantic settings classes
2. **settings/__init__.py** - Package exports
3. **engine.py** - Uses settings for display config
4. **main.py** - Loads and logs settings
5. **utils/datetime_util.py** - Uses timezone settings
6. **widgets/weather_widget.py** - Uses weather settings
7. **.env.example** - Updated with all settings
8. **pyproject.toml** - Added pydantic dependencies

## Installation

```bash
# Install/update dependencies
uv sync
```

This will install:
- `pydantic>=2.0.0`
- `pydantic-settings>=2.0.0`
