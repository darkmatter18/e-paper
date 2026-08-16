"""Engine process entry point.

This module is the entry point for the display engine when running in a
separate process. It's called by EngineProcessManager.
"""

import logging
from multiprocessing import Queue

from dotenv import load_dotenv

# Load .env before importing settings
load_dotenv()

from display import Display
from screens import get_screen
from utils.log import configure_logging

logger = logging.getLogger(__name__)


def run_display(screen_name: str, command_queue: Queue):
    """Run the engine in a separate process.

    Args:
        screen_name: Name of initial screen to display
        command_queue: Queue for receiving commands from main process
    """
    # Configure logging for this process
    configure_logging()

    logger.info(f"Engine process starting with screen '{screen_name}'")

    # Create initial screen
    screen = get_screen(screen_name)

    # Start engine with command queue
    engine = Display(screen=screen)
    try:

        engine.run(command_queue=command_queue)

    except KeyboardInterrupt:
        logger.info("Engine process received keyboard interrupt")
    except Exception:
        logger.exception("Engine process encountered fatal error")
    finally:
        # Cleanup on exit
        try:
            engine.cleanup()
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error during cleanup: {e}")

        logger.info("Engine process exiting")
