"""E-paper display clock using modular widget architecture."""
import logging
import sys
import time

from PIL import Image, ImageDraw

from lib.waveshare_epd import epd7in5b_V2
from utils import DateTimeUtil
from widgets import ClockWidget, DateWidget, QuoteWidget, WeatherWidget

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
ALL_WIDGETS = [clock_widget, date_widget, weather_widget, quote_widget]


def to_buffer(image):
    """Convert a mode-'1' image to an e-paper buffer for display_Partial.

    Unlike display() (which inverts the black bytes itself at
    epd7in5b_V2.py:209), display_Partial sends the buffer to RAM as-is. So the
    bytes must already be in hardware polarity: 1=white, 0=black -- which is
    exactly what PIL's mode-'1' tobytes() gives (white bit=1, black bit=0).
    No inversion here.
    """
    return bytearray(image.convert("1").tobytes("raw"))


def full_refresh(epd, now):
    """Full display refresh with all widgets.

    Args:
        epd: E-paper display object
        now: Current datetime

    Returns:
        Full display frame (800x480) for next partial refresh
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

    # Return full frame for next partial refresh
    return black


def get_partial_refresh_region():
    """Calculate bounding box encompassing all partial-refresh widgets.

    Returns:
        tuple: (x, y, width, height) or None if no widgets support partial refresh
    """
    regions = [w.region for w in ALL_WIDGETS if w.supports_partial_refresh]

    if not regions:
        return None

    # Calculate bounding box
    min_x = min(r.x for r in regions)
    min_y = min(r.y for r in regions)
    max_x = max(r.x + r.width for r in regions)
    max_y = max(r.y + r.height for r in regions)

    return (min_x, min_y, max_x - min_x, max_y - min_y)


def render_partial_frame(now):
    """Render full display (800x480) with only partial-refresh widgets.

    Args:
        now: Current datetime

    Returns:
        PIL Image (800x480) with partial-refresh widgets rendered
    """
    black = Image.new("1", (DISPLAY_W, DISPLAY_H), 255)
    db = ImageDraw.Draw(black)

    # Each widget renders at its own coordinates
    for widget in ALL_WIDGETS:
        if widget.supports_partial_refresh:
            widget.draw(db, red_draw=None, now=now)

    return black


def partial_refresh(epd, now, old_frame):
    """Partial refresh all widgets that support it.

    Args:
        epd: E-paper display object
        now: Current datetime
        old_frame: Previous full display frame (800x480)

    Returns:
        New full display frame (800x480)
    """
    from lib.waveshare_epd import epdconfig

    # Render new frame
    new_frame = render_partial_frame(now)

    # Get bounding region
    region = get_partial_refresh_region()
    if not region:
        return old_frame  # No partial refresh widgets

    x, y, w, h = region

    # Convert to buffers
    old_buf = to_buffer(old_frame)
    new_buf = to_buffer(new_frame)

    # Send partial refresh commands
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

    return new_frame


def clock():
    """Main clock loop - manages display updates."""

    try:
        # Initialize e-paper display
        epd = epd7in5b_V2.EPD()
        logger.info("init and Clear")
        epd.init()
        epd.Clear()

        # Track state
        last_full = None
        old_frame = None  # Track full display frame (800x480) for partial refresh

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
                old_frame = full_refresh(epd, now)
                last_full = now
                epd.sleep()
                time.sleep(60)  # Sleep for a minute after full refresh
            else:
                # Partial refresh: update all widgets that support it
                if old_frame is not None:
                    epd.init_part()
                    old_frame = partial_refresh(epd, now, old_frame)
                    epd.sleep()
                else:
                    # Fallback: if we don't have old_frame, do full refresh
                    old_frame = full_refresh(epd, now)
                    last_full = now
                    epd.sleep()

                time.sleep(60)  # Sleep for a minute

    except OSError as e:
        logger.info(e)

    except KeyboardInterrupt:
        logger.info("Exiting...")
        epd7in5b_V2.epdconfig.module_exit()
        sys.exit()
