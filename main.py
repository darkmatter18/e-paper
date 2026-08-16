"""E-paper display with FastAPI control server.

This is the main entry point that starts both:
1. FastAPI server (main process) - REST API for controlling the display
2. Display engine (child process) - Manages e-paper hardware and rendering

The API server allows switching between screens without restarting.
"""

import logging

import uvicorn
from dotenv import load_dotenv

# Load .env file before any imports
load_dotenv()

from api import create_app
from settings import get_settings
from utils.log import configure_logging

# Configure logging
configure_logging()

logger = logging.getLogger(__name__)


def main():
    """Start FastAPI server with display engine."""
    settings = get_settings()

    logger.info("=" * 60)
    logger.info("E-Paper Display - FastAPI Server")
    logger.info("=" * 60)
    logger.info(f"API Server: http://{settings.api.host}:{settings.api.port}")
    logger.info(f"Display: {settings.display.WIDTH}x{settings.display.HEIGHT}")
    logger.info(f"Log Level: {settings.logging.level}")
    logger.info("=" * 60)

    # Create FastAPI app
    app = create_app()

    # Run server
    uvicorn.run(
        app,
        host=settings.api.host,
        port=settings.api.port,
        log_config=None,  # Use our logging config
        access_log=True,
    )


if __name__ == "__main__":
    main()
