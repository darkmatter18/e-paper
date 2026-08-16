"""E-paper display rendering engine.

This module provides the Engine class which manages the complete rendering
pipeline for e-paper displays, including full refresh, partial refresh,
state management, and the main display loop.
"""

import logging
import time

from PIL import Image, ImageDraw

from lib.waveshare_epd import epd7in5b_V2
from settings import get_settings
from utils import DateTimeUtil, PartialStateManager, Screen

logger = logging.getLogger(__name__)
settings = get_settings()


class Engine:
    """Rendering engine for e-paper display.

    Manages the complete rendering pipeline including:
    - Full refresh with red channel (flashing)
    - Partial refresh for black-only updates (no flashing)
    - State management for partial refresh
    - Display timing and power management
    - Main event loop

    Attributes:
        screen (Screen): Screen instance containing widgets to render.
        epd (epd7in5b_V2.EPD): E-paper display hardware interface.
        state_manager (PartialStateManager): Tracks widget states for partial refresh.
        full_refresh_interval (int): Minutes between full refreshes (default: 15).
        display_width (int): Display width in pixels (800).
        display_height (int): Display height in pixels (480).
    """

    def __init__(self, screen: Screen):
        """Initialize rendering engine.

        Args:
            screen: Screen instance with widgets to render.

        Note:
            Display settings (width, height, refresh interval) are loaded from
            application settings via get_settings().
        """
        self.screen = screen
        self.full_refresh_interval = settings.display.full_refresh_interval
        self.display_width = settings.display.WIDTH
        self.display_height = settings.display.HEIGHT

        # Initialize hardware
        self.epd = epd7in5b_V2.EPD()
        logger.info("Initializing e-paper display")
        self.epd.init()
        self.epd.Clear()

        # Initialize state manager for partial refresh
        self.state_manager = PartialStateManager()
        self.last_full = None

    @staticmethod
    def to_buffer(image: Image.Image) -> bytearray:
        """Convert PIL Image to e-paper buffer with correct polarity.

        CRITICAL: Unlike display() which inverts the buffer internally,
        display_Partial() sends data as-is. Buffer must be in hardware
        polarity (1=white, 0=black), which PIL mode-'1' provides directly.

        Args:
            image: PIL Image in any mode (converted to mode '1' if needed).

        Returns:
            bytearray suitable for e-paper partial refresh commands (0x10, 0x13).
        """
        return bytearray(image.convert("1").tobytes("raw"))

    @staticmethod
    def extract_region(
        image: Image.Image, x: int, y: int, width: int, height: int
    ) -> Image.Image:
        """Extract rectangular region from full display image.

        Args:
            image: Full display PIL Image (typically 800x480 in mode '1').
            x: Left edge of region in pixels (0-799).
            y: Top edge of region in pixels (0-479).
            width: Width of region in pixels.
            height: Height of region in pixels.

        Returns:
            Cropped PIL Image of size (width, height).
        """
        return image.crop((x, y, x + width, y + height))

    def full_refresh(self) -> None:
        """Perform full display refresh with all widgets including red channel.

        Full refresh (flashing) is required to activate or erase red pigment.
        Renders all widgets to both black and red channels, displays to hardware,
        then extracts and stores regions for subsequent partial refreshes.

        Side Effects:
            - Initializes display hardware (epd.init())
            - Sends full display data to e-paper controller
            - Updates state_manager with regions for all partial-refresh widgets
            - Display briefly flashes black/white/red during update
        """
        logger.info("Starting full refresh (all widgets with red channel)")
        self.epd.init()

        # Create white canvases for both channels (255 = white in mode '1')
        black = Image.new("1", (self.epd.width, self.epd.height), 255)
        red = Image.new("1", (self.epd.width, self.epd.height), 255)
        db = ImageDraw.Draw(black)
        dr = ImageDraw.Draw(red)

        # Render all widgets with content, decorations, and red accents
        for widget in self.screen:
            widget.draw(db, dr)
            widget.draw_decorations(db)
            widget.draw_red_decorations(dr)

        # Send both buffers to e-paper controller and update display
        self.epd.display(self.epd.getbuffer(black), self.epd.getbuffer(red))

        # Extract and store regions for partial-refresh widgets
        self.state_manager.update_from_full_frame(
            black, self.screen.get_all_widgets(), self.extract_region
        )

        logger.info("Full refresh completed successfully")

    def partial_refresh(self) -> None:
        """Perform partial refresh for widgets that support it (black channel only).

        Partial refresh updates only changed pixels without flashing, but can only
        modify the black channel. Each widget with supports_partial_refresh=True
        is refreshed independently with region-specific buffers.

        Side Effects:
            - Sends partial refresh commands to e-paper controller for each widget
            - Updates state_manager with new regions for next partial refresh
            - Display updates without flashing (only changed pixels)
            - Each widget refresh takes ~100ms for controller processing
        """
        logger.info(f"Starting partial refresh ({self.screen} widgets)")

        from lib.waveshare_epd import epdconfig

        partial_widgets = self.screen.get_partial_refresh_widgets()

        refreshed_count = 0
        # Iterate through all widgets that support partial refresh
        for widget in partial_widgets:
            # Retrieve previous region state for comparison
            old_region = self.state_manager.get_old_region(widget)
            if old_region is None:
                logger.warning(
                    f"No previous state for {widget.__class__.__name__}, skipping"
                )
                continue

            # Render widget to temporary full-size image
            region = widget.region
            temp_full = Image.new("1", (self.display_width, self.display_height), 255)
            temp_draw = ImageDraw.Draw(temp_full)
            widget.draw(temp_draw, red_draw=None)

            # Extract only the widget's region from temporary image
            new_region = self.extract_region(
                temp_full, region.x, region.y, region.width, region.height
            )

            # Convert PIL images to e-paper buffers with correct polarity
            old_buf = self.to_buffer(old_region)
            new_buf = self.to_buffer(new_region)

            # Prepare region coordinates for e-paper controller
            x, y, w, h = region.x, region.y, region.width, region.height

            # Send low-level partial refresh commands to e-paper controller
            self.epd.send_command(0x91)  # Enter partial refresh mode
            self.epd.send_command(0x90)  # Set partial window
            self.epd.send_data(x // 256)  # X start high byte
            self.epd.send_data(x % 256)  # X start low byte
            self.epd.send_data((x + w - 1) // 256)  # X end high byte
            self.epd.send_data((x + w - 1) % 256)  # X end low byte
            self.epd.send_data(y // 256)  # Y start high byte
            self.epd.send_data(y % 256)  # Y start low byte
            self.epd.send_data((y + h - 1) // 256)  # Y end high byte
            self.epd.send_data((y + h - 1) % 256)  # Y end low byte
            self.epd.send_data(0x01)  # Scan mode

            self.epd.send_command(0x10)  # Write old data to RAM
            self.epd.send_data2(old_buf)

            self.epd.send_command(0x13)  # Write new data to RAM
            self.epd.send_data2(new_buf)

            self.epd.send_command(0x12)  # Trigger display refresh
            epdconfig.delay_ms(100)  # Wait for controller processing
            self.epd.ReadBusy()  # Wait for refresh completion

            # Store new region for next partial refresh cycle
            self.state_manager.update_state(widget, new_region)
            refreshed_count += 1

        logger.info(f"Partial refresh completed ({refreshed_count}/{len(partial_widgets)} widgets updated)")

    def run(self) -> None:
        """Main rendering loop - manages display update cycles.

        Orchestrates the display refresh strategy:
        - Full refresh every N minutes and at top of hour
        - Partial refresh every minute between full refreshes
        - Power management (display sleep between updates)
        - Timing alignment to minute boundaries

        The loop runs indefinitely until KeyboardInterrupt or hardware error.

        Raises:
            SystemExit: On KeyboardInterrupt or fatal error.

        Side Effects:
            - Controls e-paper display hardware
            - Runs indefinitely (blocking call)
            - Logs refresh cycles and errors
        """
        try:
            while True:
                # Get current time in IST timezone
                now = DateTimeUtil.now()
                minute = now.minute

                # Determine refresh type based on time and interval
                need_full = (
                    self.last_full is None  # First run
                    or minute % self.full_refresh_interval == 0  # Interval reached
                    or minute == 0  # Top of every hour
                )

                if need_full:
                    # Full refresh: all widgets with red channel
                    self.full_refresh()
                    self.last_full = now
                    self.epd.sleep()
                else:
                    # Partial refresh: only widgets that support it (black channel)
                    if self.state_manager.has_state():
                        self.epd.init_part()
                        self.partial_refresh()
                        self.epd.sleep()
                    else:
                        # Fallback: no previous state, do full refresh
                        logger.warning(
                            "No state for partial refresh, falling back to full refresh"
                        )
                        self.full_refresh()
                        self.last_full = now
                        self.epd.sleep()

                # Calculate sleep time to wake at start of next minute
                now_after_render = DateTimeUtil.now()
                seconds_elapsed = now_after_render.second + (
                    now_after_render.microsecond / 1_000_000
                )
                sleep_time = 60 - seconds_elapsed

                # Ensure we always sleep at least a little to avoid tight loop
                if sleep_time < 0.1:
                    sleep_time = 60 + sleep_time  # Move to next minute

                logger.info(f"Sleeping for {sleep_time:.2f}s until next minute")
                time.sleep(sleep_time)

        except OSError as e:
            logger.error(f"Hardware error: {e}")


    def cleanup(self) -> None:
        """Clean up display hardware resources.

        Should be called before program exit to properly release GPIO pins.
        """
        logger.info("Cleaning up display hardware")
        epd7in5b_V2.epdconfig.module_exit()
