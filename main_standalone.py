"""E-paper display clock application entry point."""

import logging

from dotenv import load_dotenv

# Load .env file into os.environ before any imports that call get_settings()
# Pydantic BaseSettings reads from os.environ, not directly from .env file
load_dotenv()

from display import Display
from screens import DEFAULT_SCREEN, get_screen
from settings import get_settings
from utils.log import configure_logging

# Get settings
settings = get_settings()

# Configure logging
configure_logging()

logger = logging.getLogger(__name__)


def main():
    """Initialize and run the e-paper clock display."""
    # Create screen (using default screen from screens module)
    screen = get_screen(DEFAULT_SCREEN)

    logger.info(f"Starting e-paper clock with screen '{screen.name}'")
    logger.info(f"Widgets: {[w.__class__.__name__ for w in screen.widgets]}")
    logger.info(f"Display: {settings.display.WIDTH}x{settings.display.HEIGHT} (Waveshare 7.5\" B/V2)")
    logger.info(f"Full refresh interval: {settings.display.full_refresh_interval} minutes")
    logger.info(f"Timezone: {settings.timezone.name} (UTC+{settings.timezone.utc_offset_hours}:{settings.timezone.utc_offset_minutes:02d})")

    # Create and run rendering engine
    engine = Display(screen=screen)

    try: 
        engine.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        engine.cleanup()
    except Exception:
        logger.exception("Unexpected error occurred")


if __name__ == "__main__":
    main()
