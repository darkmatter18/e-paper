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

# Initialize widgets (done in clock() function after services are created)
clock_widget = ClockWidget()
date_widget = DateWidget()
quote_widget = QuoteWidget()
weather_widget = WeatherWidget()


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
        Clock region image (400x240) for next partial refresh
    """
    logger.info("Full refresh")
    epd.init()

    # Create black and red canvases
    black = Image.new("1", (epd.width, epd.height), 255)
    red = Image.new("1", (epd.width, epd.height), 255)
    db = ImageDraw.Draw(black)
    dr = ImageDraw.Draw(red)

    # Draw all widgets with their content
    clock_widget.draw(db, red_draw=dr, now=now)
    clock_widget.draw_decorations(db)
    clock_widget.draw_red_decorations(dr)

    date_widget.draw(db, red_draw=dr)
    date_widget.draw_decorations(db)
    date_widget.draw_red_decorations(dr)

    weather_widget.draw(db, red_draw=dr)
    weather_widget.draw_decorations(db)
    weather_widget.draw_red_decorations(dr)

    quote_widget.draw(db)
    quote_widget.draw_decorations(db)
    quote_widget.draw_red_decorations(dr)

    # Display to e-paper
    epd.display(epd.getbuffer(black), epd.getbuffer(red))

    # Return the clock region for next partial refresh
    return render_clock_region(now)


def render_clock_region(now):
    """Render just the clock region (400x240) for partial refresh.

    Args:
        now: Current datetime

    Returns:
        PIL Image of clock region only
    """
    # Create image for clock region only (not full display)
    region = Image.new("1", (400, 240), 255)
    db = ImageDraw.Draw(region)

    # Draw clock widget into the region
    clock_widget.draw(db, red_draw=None, now=now)

    return region


def partial_refresh_with_old(epd, now, old_region):
    """Partial refresh - update only the clock (minute hand) in black.

    Args:
        epd: E-paper display object
        now: Current datetime
        old_region: Previous clock region image (400x240) for comparison

    Returns:
        Updated clock region image
    """
    from lib.waveshare_epd import epdconfig

    # Render new clock region
    new_region = render_clock_region(now)

    # Clock region coordinates (upper-left quadrant: 0,0 to 400,240)
    region_x, region_y = 0, 0
    region_w, region_h = 400, 240

    # Convert old and new REGION images to buffers
    old_buf = to_buffer(old_region)
    new_buf = to_buffer(new_region)

    # Send partial refresh commands to e-paper controller
    # This sends both old and new buffers so controller knows which pixels to update
    Xstart = region_x
    Ystart = region_y
    Xend = region_x + region_w
    Yend = region_y + region_h

    epd.send_command(0x91)
    epd.send_command(0x90)
    epd.send_data(Xstart // 256)
    epd.send_data(Xstart % 256)
    epd.send_data((Xend - 1) // 256)
    epd.send_data((Xend - 1) % 256)
    epd.send_data(Ystart // 256)
    epd.send_data(Ystart % 256)
    epd.send_data((Yend - 1) // 256)
    epd.send_data((Yend - 1) % 256)
    epd.send_data(0x01)

    epd.send_command(0x10)  # Send old buffer
    epd.send_data2(old_buf)

    epd.send_command(0x13)  # Send new buffer
    epd.send_data2(new_buf)

    epd.send_command(0x12)  # Refresh
    epdconfig.delay_ms(100)
    epd.ReadBusy()

    return new_region


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
        old_region = None  # Track clock region (400x240) for partial refresh

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
                old_region = full_refresh(epd, now)
                last_full = now
                epd.sleep()
                time.sleep(60)  # Sleep for a minute after full refresh
            else:
                # Partial refresh: only update clock minute hand
                if old_region is not None:
                    epd.init_part()
                    old_region = partial_refresh_with_old(epd, now, old_region)
                    epd.sleep()
                else:
                    # Fallback: if we don't have old_region, do full refresh
                    old_region = full_refresh(epd, now)
                    last_full = now
                    epd.sleep()

                time.sleep(60)  # Sleep for a minute

    except OSError as e:
        logger.info(e)

    except KeyboardInterrupt:
        logger.info("Exiting...")
        epd7in5b_V2.epdconfig.module_exit()
        sys.exit()
