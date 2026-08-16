"""E-paper display clock application entry point."""

import logging

from dotenv import load_dotenv

from engine import Engine
from utils import Screen
from utils.log import configure_logging
from widgets import ClockWidget, DateWidget, QuoteWidget, WeatherWidget

# Load environment variables
load_dotenv()

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

    # Create and run rendering engine
    engine = Engine(screen=clock_screen, full_refresh_interval=15)
    engine.run()


if __name__ == "__main__":
    main()
