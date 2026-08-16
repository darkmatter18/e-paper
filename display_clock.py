"""E-paper display clock using modular widget architecture."""

import logging
import sys
import time

from PIL import Image, ImageDraw

from lib.waveshare_epd import epd7in5b_V2
from utils import DateTimeUtil
from widgets import ClockWidget, DateWidget, QuoteWidget, WeatherWidget
from widgets.widget import Widget

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Display dimensions
DISPLAY_W, DISPLAY_H = 800, 480

# How often to do a full (flashing) refresh. Red only renders on a full
# refresh, so this is when the red elements are redrawn.
# Between full refreshes the minute hand moves in black via partial refresh.
FULL_REFRESH_MIN = 15

# Initialize widgets
clock_widget = ClockWidget()
date_widget = DateWidget()
quote_widget = QuoteWidget()
weather_widget = WeatherWidget()

# All widgets for rendering
ALL_WIDGETS: list[Widget] = [clock_widget, date_widget, weather_widget, quote_widget]


class PartialStateManager:
    """Manages previous state for partial refresh widgets."""

    def __init__(self):
        """Initialize state manager with empty state."""
        self._states = {}  # widget -> previous region image

    def get_old_region(self, widget):
        """Get previous region image for a widget.

        Args:
            widget: Widget to get state for

        Returns:
            PIL Image of previous region, or None if no previous state
        """
        return self._states.get(widget)

    def update_state(self, widget, new_region):
        """Update stored state for a widget.

        Args:
            widget: Widget to update state for
            new_region: New region image to store
        """
        self._states[widget] = new_region.copy()

    def update_from_full_frame(self, full_frame):
        """Extract and store regions for all partial-refresh widgets from full frame.

        Args:
            full_frame: Full display image (800x480)
        """
        for widget in ALL_WIDGETS:
            if widget.supports_partial_refresh:
                region = widget.region
                extracted = extract_region(
                    full_frame, region.x, region.y, region.width, region.height
                )
                self.update_state(widget, extracted)

    def has_state(self):
        """Check if manager has any stored state.

        Returns:
            True if any widget state is stored
        """
        return len(self._states) > 0


def to_buffer(image):
    """Convert a mode-'1' image to an e-paper buffer for display_Partial.

    Unlike display() (which inverts the black bytes itself at
    epd7in5b_V2.py:209), display_Partial sends the buffer to RAM as-is. So the
    bytes must already be in hardware polarity: 1=white, 0=black -- which is
    exactly what PIL's mode-'1' tobytes() gives (white bit=1, black bit=0).
    No inversion here.
    """
    return bytearray(image.convert("1").tobytes("raw"))


def full_refresh(epd, now, state_manager):
    """Full display refresh with all widgets.

    Args:
        epd: E-paper display object
        now: Current datetime
        state_manager: PartialStateManager to update with new state
    """
    logger.info("Full refresh")
    epd.init()

    # Create black and red canvases
    black = Image.new("1", (epd.width, epd.height), 255)
    red = Image.new("1", (epd.width, epd.height), 255)
    db = ImageDraw.Draw(black)
    dr = ImageDraw.Draw(red)

    # Draw all widgets with their content
    for widget in ALL_WIDGETS:
        widget.draw(db, dr, now=now)
        widget.draw_decorations(db)
        widget.draw_red_decorations(dr)

    # Display to e-paper
    epd.display(epd.getbuffer(black), epd.getbuffer(red))

    # Update state manager with new widget states
    state_manager.update_from_full_frame(black)


def extract_region(image, x, y, width, height):
    """Extract a region from a full display image.

    Args:
        image: Full display image (800x480)
        x: Region left edge
        y: Region top edge
        width: Region width
        height: Region height

    Returns:
        PIL Image of just the region
    """
    return image.crop((x, y, x + width, y + height))


def partial_refresh(epd, now, state_manager):
    """Partial refresh all widgets that support it.

    Each widget's region is refreshed independently with region-specific buffers.

    Args:
        epd: E-paper display object
        now: Current datetime
        state_manager: PartialStateManager with previous widget states
    """
    from lib.waveshare_epd import epdconfig

    # Refresh each partial-refresh widget independently
    for widget in ALL_WIDGETS:
        if not widget.supports_partial_refresh:
            continue

        # Get old region from state manager
        old_region = state_manager.get_old_region(widget)
        if old_region is None:
            logger.warning(
                f"No previous state for {widget.__class__.__name__}, skipping partial refresh"
            )
            continue

        # Render new region for this widget
        # Widget draws at its coordinates in full display space
        # We need to create a temporary full-size image, let widget draw, then extract region
        region = widget.region
        temp_full = Image.new("1", (DISPLAY_W, DISPLAY_H), 255)
        temp_draw = ImageDraw.Draw(temp_full)
        widget.draw(temp_draw, red_draw=None, now=now)

        # Extract the widget's region from temp image
        new_region = extract_region(
            temp_full, region.x, region.y, region.width, region.height
        )

        # Convert region images to buffers
        old_buf = to_buffer(old_region)
        new_buf = to_buffer(new_region)

        # Send partial refresh commands for this widget's region
        x, y, w, h = region.x, region.y, region.width, region.height

        epd.send_command(0x91)
        epd.send_command(0x90)
        epd.send_data(x // 256)
        epd.send_data(x % 256)
        epd.send_data((x + w - 1) // 256)
        epd.send_data((x + w - 1) % 256)
        epd.send_data(y // 256)
        epd.send_data(y % 256)
        epd.send_data((y + h - 1) // 256)
        epd.send_data((y + h - 1) % 256)
        epd.send_data(0x01)

        epd.send_command(0x10)  # Old buffer
        epd.send_data2(old_buf)

        epd.send_command(0x13)  # New buffer
        epd.send_data2(new_buf)

        epd.send_command(0x12)  # Refresh
        epdconfig.delay_ms(100)
        epd.ReadBusy()

        # Update state manager with new region
        state_manager.update_state(widget, new_region)


def clock():
    """Main clock loop - manages display updates."""

    try:
        # Initialize e-paper display
        epd = epd7in5b_V2.EPD()
        logger.info("init and Clear")
        epd.init()
        epd.Clear()

        # Initialize state manager
        state_manager = PartialStateManager()
        last_full = None

        while True:
            now = DateTimeUtil.now()
            minute = now.minute

            # Decide: full refresh or partial refresh?
            need_full = (
                last_full is None  # First run
                or minute % FULL_REFRESH_MIN == 0  # Every 15 minutes
                or now.minute == 0  # Top of the hour (to update red elements)
            )

            if need_full:
                full_refresh(epd, now, state_manager)
                last_full = now
                epd.sleep()
                time.sleep(60)  # Sleep for a minute after full refresh
            else:
                # Partial refresh: update all widgets that support it
                if state_manager.has_state():
                    epd.init_part()
                    partial_refresh(epd, now, state_manager)
                    epd.sleep()
                else:
                    # Fallback: if we don't have previous state, do full refresh
                    full_refresh(epd, now, state_manager)
                    last_full = now
                    epd.sleep()

                time.sleep(60)  # Sleep for a minute

    except OSError as e:
        logger.info(e)

    except KeyboardInterrupt:
        logger.info("Exiting...")
        epd7in5b_V2.epdconfig.module_exit()
        sys.exit()
