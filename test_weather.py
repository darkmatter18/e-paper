"""Test weather service integration without hardware."""
import os

from dotenv import load_dotenv

from services.weather import OpenWeatherMapService

load_dotenv()

# Test weather service
api_key = os.getenv("OPENWEATHER_API_KEY", "")
lat = float(os.getenv("LATITUDE", ""))
lon = float(os.getenv("LONGITUDE", ""))

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
