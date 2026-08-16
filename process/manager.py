"""Engine process manager for running display engine in separate process."""

import logging
from multiprocessing import Process, Queue

logger = logging.getLogger(__name__)


class EngineProcessManager:
    """Manages the display engine in a separate process.

    Attributes:
        command_queue: Queue for sending commands to engine process
        engine_process: Process running the engine
        current_screen: Name of currently displayed screen
    """

    def __init__(self, initial_screen: str = "datetime_weather_forecast"):
        """Initialize engine process manager.

        Args:
            initial_screen: Name of screen to start with
        """
        self.command_queue: Queue = Queue()
        self.engine_process: Process | None = None
        self.current_screen = initial_screen

    def start_engine(self):
        """Start the engine process."""
        from display.display_main import run_display

        self.engine_process = Process(
            target=run_display,
            args=(self.current_screen, self.command_queue),
            name="DisplayProcess",
            daemon=False,  # Allow graceful shutdown
        )
        self.engine_process.start()
        logger.info(f"Engine process started (PID: {self.engine_process.pid})")

    def stop_engine(self, timeout: float = 10.0):
        """Stop the engine process gracefully.

        Args:
            timeout: Seconds to wait for graceful shutdown before force termination
        """
        if self.engine_process and self.engine_process.is_alive():
            logger.info("Sending shutdown command to engine...")
            self.command_queue.put({"type": "shutdown"})
            self.engine_process.join(timeout=timeout)

            if self.engine_process.is_alive():
                logger.warning("Engine did not stop gracefully, terminating...")
                self.engine_process.terminate()
                self.engine_process.join(timeout=2)

            logger.info("Engine process stopped")

    def switch_screen(self, screen_name: str):
        """Send command to switch screen.

        Args:
            screen_name: Name of screen from AVAILABLE_SCREENS registry

        Raises:
            RuntimeError: If engine process is not running
        """
        if not self.is_alive():
            raise RuntimeError("Engine process is not running")

        logger.info(f"Sending switch_screen command: {screen_name}")
        self.command_queue.put({"type": "switch_screen", "screen_name": screen_name})
        self.current_screen = screen_name

    def is_alive(self) -> bool:
        """Check if engine process is running.

        Returns:
            True if engine process is alive, False otherwise
        """
        return self.engine_process is not None and self.engine_process.is_alive()
