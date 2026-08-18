from collections.abc import Callable  # noqa: N999

from screens.datetime_weather_forecast import create_datetime_weather_forecast_screen
from screens.todays_weather import create_todays_weather_screen
from utils.screen import Screen

# Screen registry - maps screen names to factory functions
AVAILABLE_SCREENS: dict[str, Callable[[], Screen]] = {
    "datetime_weather_forecast": create_datetime_weather_forecast_screen,
    "todays_weather": create_todays_weather_screen,
}

# Default screen name
DEFAULT_SCREEN = "datetime_weather_forecast"


def get_screen(name: str) -> Screen:
    """get a screen by name.

    Args:
        name: Screen name from AVAILABLE_SCREENS.

    Returns:
        Screen instance with configured widgets.

    Raises:
        KeyError: If screen name not found in AVAILABLE_SCREENS.
    """
    if name not in AVAILABLE_SCREENS:
        raise KeyError(
            f"Unknown screen '{name}'. Available: {list(AVAILABLE_SCREENS.keys())}"
        )

    factory = AVAILABLE_SCREENS[name]
    return factory()


__all__ = [
    "AVAILABLE_SCREENS",
    "DEFAULT_SCREEN",
    "get_screen",
]
