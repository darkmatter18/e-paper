"""E-paper display clock using modular widget architecture."""

import logging
import sys
import time

from PIL import Image, ImageDraw

from lib.waveshare_epd import epd7in5b_V2
from utils import DateTimeUtil, PartialStateManager
from widgets import ClockWidget, DateWidget, QuoteWidget, WeatherWidget, Widget

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


def to_buffer(image: Image.Image) -> bytearray:
    """Convert a PIL Image to e-paper buffer with correct polarity for partial refresh.

    CRITICAL: Unlike display() which inverts the buffer internally (epd7in5b_V2.py:209),
    display_Partial() sends data to controller RAM as-is. Therefore, the buffer must
    already be in hardware polarity (1=white pixel, 0=black pixel), which PIL's mode-'1'
    tobytes() provides directly. No inversion is performed here.

    Args:
        image: PIL Image in any mode (will be converted to mode '1' if needed).
               Mode '1' uses 1 bit per pixel: 1=white, 0=black.

    Returns:
        bytearray suitable for e-paper partial refresh commands (0x10, 0x13).
        Each byte contains 8 pixels in hardware polarity.

    Note:
        For full refresh, use epd.getbuffer() instead, which handles inversion.
    """
    return bytearray(image.convert("1").tobytes("raw"))


def full_refresh(epd: epd7in5b_V2.EPD, now, state_manager: PartialStateManager) -> None:
    """Perform full display refresh with all widgets including red channel.

    Full refresh (flashing) is required to activate or erase red pigment on the
    e-paper display. Renders all widgets to both black and red channels, displays
    to hardware, then extracts and stores regions for subsequent partial refreshes.

    Occurs every 15 minutes and at the top of every hour to keep red elements crisp.

    Args:
        epd: Waveshare EPD display object (epd7in5b_V2.EPD instance).
        now: Current datetime object (timezone-aware, IST). Passed to widgets
             for rendering time-dependent content.
        state_manager: PartialStateManager instance to update with new widget
                      states for next partial refresh cycle.

    Side Effects:
        - Initializes display hardware (epd.init())
        - Sends full display data to e-paper controller
        - Updates state_manager with regions for all partial-refresh widgets
        - Display briefly flashes black/white/red during update

    Note:
        Display should be put to sleep (epd.sleep()) after this call to save power.
    """
    logger.info("Full refresh")
    epd.init()

    # Create white canvases for both channels (255 = white in mode '1')
    black = Image.new("1", (epd.width, epd.height), 255)
    red = Image.new("1", (epd.width, epd.height), 255)
    db = ImageDraw.Draw(black)
    dr = ImageDraw.Draw(red)

    # Render all widgets with content, decorations, and red accents
    for widget in ALL_WIDGETS:
        widget.draw(db, dr, now=now)
        widget.draw_decorations(db)
        widget.draw_red_decorations(dr)

    # Send both buffers to e-paper controller and update display
    epd.display(epd.getbuffer(black), epd.getbuffer(red))

    # Extract and store regions for partial-refresh widgets
    state_manager.update_from_full_frame(black, ALL_WIDGETS, extract_region)


def extract_region(image: Image.Image, x: int, y: int, width: int, height: int) -> Image.Image:
    """Extract a rectangular region from a full display image.

    Used to crop widget regions from full 800x480 display for partial refresh.
    The extracted region maintains the same mode as the source image.

    Args:
        image: Full display PIL Image (typically 800x480 in mode '1').
        x: Left edge of region in pixels (0-799).
        y: Top edge of region in pixels (0-479).
        width: Width of region in pixels.
        height: Height of region in pixels.

    Returns:
        Cropped PIL Image of size (width, height) containing only the specified
        region. The returned image is a view/copy depending on PIL internals.
    """
    return image.crop((x, y, x + width, y + height))


def partial_refresh(epd: epd7in5b_V2.EPD, now, state_manager: PartialStateManager) -> None:
    """Perform partial refresh for all widgets that support it (black channel only).

    Partial refresh updates only changed pixels without flashing, but can only modify
    the black channel. Each widget with supports_partial_refresh=True is refreshed
    independently with region-specific buffers matching the widget's exact dimensions.

    The e-paper controller compares old and new buffers to determine which pixels
    to update, so buffer size MUST match region coordinates exactly.

    Args:
        epd: Waveshare EPD display object (epd7in5b_V2.EPD instance), must be
             initialized for partial refresh (epd.init_part()).
        now: Current datetime object (timezone-aware, IST). Passed to widgets
             for rendering time-dependent content.
        state_manager: PartialStateManager containing previous regions for comparison.
                      If no previous state exists for a widget, that widget is skipped.

    Side Effects:
        - Sends partial refresh commands to e-paper controller for each widget
        - Updates state_manager with new regions for next partial refresh
        - Display updates without flashing (only changed pixels)
        - Each widget refresh takes ~100ms for controller processing

    Process:
        1. For each widget with supports_partial_refresh=True:
           a. Get old region from state manager
           b. Render widget to temporary full-size image
           c. Extract widget's region from temporary image
           d. Send old + new buffers to controller with region coordinates
           e. Controller compares buffers and updates only changed pixels
           f. Store new region in state manager for next refresh

    Note:
        - Only black channel is updated (red_draw=None passed to widgets)
        - Display should be put to sleep (epd.sleep()) after this call
        - If state_manager.has_state() is False, this will skip all widgets
    """
    from lib.waveshare_epd import epdconfig

    # Iterate through all widgets, refreshing only those that support it
    for widget in ALL_WIDGETS:
        if not widget.supports_partial_refresh:
            continue

        # Retrieve previous region state for comparison
        old_region = state_manager.get_old_region(widget)
        if old_region is None:
            logger.warning(
                f"No previous state for {widget.__class__.__name__}, skipping partial refresh"
            )
            continue

        # Render widget to temporary full-size image
        # Widget draws at its absolute coordinates in full display space
        region = widget.region
        temp_full = Image.new("1", (DISPLAY_W, DISPLAY_H), 255)
        temp_draw = ImageDraw.Draw(temp_full)
        widget.draw(temp_draw, red_draw=None, now=now)

        # Extract only the widget's region from temporary image
        new_region = extract_region(
            temp_full, region.x, region.y, region.width, region.height
        )

        # Convert PIL images to e-paper buffers with correct polarity
        old_buf = to_buffer(old_region)
        new_buf = to_buffer(new_region)

        # Prepare region coordinates for e-paper controller
        x, y, w, h = region.x, region.y, region.width, region.height

        # Send low-level partial refresh commands to e-paper controller
        # Reference: Waveshare e-paper controller command set
        epd.send_command(0x91)  # Enter partial refresh mode
        epd.send_command(0x90)  # Set partial window
        epd.send_data(x // 256)           # X start high byte
        epd.send_data(x % 256)            # X start low byte
        epd.send_data((x + w - 1) // 256) # X end high byte
        epd.send_data((x + w - 1) % 256)  # X end low byte
        epd.send_data(y // 256)           # Y start high byte
        epd.send_data(y % 256)            # Y start low byte
        epd.send_data((y + h - 1) // 256) # Y end high byte
        epd.send_data((y + h - 1) % 256)  # Y end low byte
        epd.send_data(0x01)               # Scan mode

        epd.send_command(0x10)  # Write old data to RAM
        epd.send_data2(old_buf)

        epd.send_command(0x13)  # Write new data to RAM
        epd.send_data2(new_buf)

        epd.send_command(0x12)  # Trigger display refresh
        epdconfig.delay_ms(100) # Wait for controller processing
        epd.ReadBusy()          # Wait for refresh completion

        # Store new region for next partial refresh cycle
        state_manager.update_state(widget, new_region)


def clock() -> None:
    """Main clock loop - manages e-paper display update cycles.

    Orchestrates the display refresh strategy:
    - Full refresh (with red channel) every 15 minutes and at top of hour
    - Partial refresh (black only) every minute between full refreshes
    - Power management (display sleep between updates)

    The loop runs indefinitely until KeyboardInterrupt (Ctrl+C) or hardware error.

    Refresh Strategy:
        Full refresh occurs when:
        - First run (initializes state manager)
        - Every 15 minutes (minute % 15 == 0)
        - Top of every hour (minute == 0)

        Partial refresh occurs:
        - All other minutes
        - Only if state_manager has previous state
        - Falls back to full refresh if no state available

    Power Management:
        - Display sleeps (low power mode) between updates
        - 60-second sleep between refresh cycles
        - Reduces power consumption and extends display lifetime

    Error Handling:
        - OSError: Logs error and exits (typically hardware communication failure)
        - KeyboardInterrupt: Clean shutdown with module exit

    Raises:
        SystemExit: On KeyboardInterrupt or fatal error.

    Side Effects:
        - Initializes and controls e-paper display hardware
        - Creates and manages PartialStateManager instance
        - Runs indefinitely (blocking call)
        - Logs refresh cycles and errors
    """

    try:
        # Initialize e-paper display hardware
        epd = epd7in5b_V2.EPD()
        logger.info("init and Clear")
        epd.init()
        epd.Clear()

        # Initialize state manager for partial refresh tracking
        state_manager = PartialStateManager()
        last_full = None  # Track when last full refresh occurred

        while True:
            # Get current time in IST timezone
            now = DateTimeUtil.now()
            minute = now.minute

            # Determine refresh type based on time and interval
            need_full = (
                last_full is None  # First run after initialization
                or minute % FULL_REFRESH_MIN == 0  # Every 15 minutes (0, 15, 30, 45)
                or now.minute == 0  # Top of every hour (ensures red elements stay crisp)
            )

            if need_full:
                # Full refresh: all widgets with red channel
                full_refresh(epd, now, state_manager)
                last_full = now
                epd.sleep()  # Put display in low-power mode
                time.sleep(60)  # Wait one minute before next cycle
            else:
                # Partial refresh: only widgets that support it (black channel)
                if state_manager.has_state():
                    epd.init_part()  # Initialize display for partial refresh
                    partial_refresh(epd, now, state_manager)
                    epd.sleep()
                else:
                    # Fallback: no previous state available, do full refresh
                    logger.warning("No state available for partial refresh, falling back to full refresh")
                    full_refresh(epd, now, state_manager)
                    last_full = now
                    epd.sleep()

                time.sleep(60)  # Wait one minute before next cycle

    except OSError as e:
        # Hardware communication error (SPI/GPIO issue)
        logger.error(f"Hardware error: {e}")

    except KeyboardInterrupt:
        # User requested shutdown (Ctrl+C)
        logger.info("Exiting...")
        epd7in5b_V2.epdconfig.module_exit()  # Clean up GPIO
        sys.exit()
