"""E-paper display clock application entry point."""

import logging

from dotenv import load_dotenv

# Load .env file into os.environ before any imports that call get_settings()
# Pydantic BaseSettings reads from os.environ, not directly from .env file
load_dotenv()

from engine import Engine
from settings import get_settings
from utils import Screen
from utils.log import configure_logging
from widgets import ClockWidget, DateWidget, QuoteWidget, WeatherWidget

# Get settings
settings = get_settings()

# Configure logging
configure_logging()

logger = logging.getLogger(__name__)


def main():
    """Initialize and run the e-paper clock display."""
    # Create main clock screen with all widgets
    clock_screen = Screen(
        widgets=[
            ClockWidget(),
            DateWidget(),
            WeatherWidget(),
            QuoteWidget(),
        ],
        name="clock"
    )

    logger.info(f"Starting e-paper clock with {len(clock_screen)} widgets")
    logger.info(f"Display: {settings.display.WIDTH}x{settings.display.HEIGHT} (Waveshare 7.5\" B/V2)")
    logger.info(f"Full refresh interval: {settings.display.full_refresh_interval} minutes")
    logger.info(f"Timezone: {settings.timezone.name} (UTC+{settings.timezone.utc_offset_hours}:{settings.timezone.utc_offset_minutes:02d})")


    # Create and run rendering engine
    engine = Engine(screen=clock_screen)

    try: 
        engine.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        engine.cleanup()
    except Exception:
        logger.exception("Unexpected error occurred")


if __name__ == "__main__":
    main()
