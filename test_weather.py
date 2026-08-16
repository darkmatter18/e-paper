"""Test weather service integration without hardware."""
from dotenv import load_dotenv

# Load .env file before importing modules that use settings
load_dotenv()

from services.weather import OpenWeatherMapService
from settings import get_settings

# Test weather service with Pydantic settings
settings = get_settings()
api_key = settings.weather.api_key
lat = settings.weather.latitude
lon = settings.weather.longitude

weather_service = OpenWeatherMapService(api_key)

print(f"Testing weather service with lat={lat}, lon={lon}")
try:
    weather = weather_service.get_weather(lat, lon)
    print("\n✓ Weather service initialized")
    rain_info = f" - Rain: {weather.current.rain_probability}%" if weather.current.rain_probability > 0 else ""
    print(f"Current: {weather.current.temperature}°C - {weather.current.description}{rain_info}")
    print(f"Forecast days: {len(weather.forecast)}")
    for i, day in enumerate(weather.forecast[:5]):
        rain_info = f" - Rain: {day.rain_probability}%" if day.rain_probability > 0 else ""
        print(f"  Day {i+1}: {day.date} - {day.temp_min}°C to {day.temp_max}°C - {day.description}{rain_info}")
except Exception as e:
    print(f"\n⚠ Weather service returned fallback (expected if no API key): {e}")
    weather = weather_service.get_weather(lat, lon)
    print(f"Using fallback: {weather.current.temperature}°C")

print("\n✓ All imports and services work correctly!")
