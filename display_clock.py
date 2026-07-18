import logging
import math
import time
from datetime import datetime

from PIL import Image, ImageDraw

from lib.waveshare_epd import epd7in5b_V2

logging.basicConfig(level=logging.DEBUG)

# --- Clock geometry (display is 800x480) ---
CX, CY = 400, 240          # center of the clock face
RADIUS = 200               # outer circle radius
HOUR_LEN = 110             # hour hand length
MIN_LEN = 175              # minute hand length
HUB_R = 8                  # center hub radius

# How often to do a full (flashing) refresh. Red only renders on a full
# refresh, so this is when the red hour hand is redrawn.
# Between full refreshes the minute hand moves in black via partial refresh.
FULL_REFRESH_MIN = 15


def hand_endpoint(length, value, total):
    """Point at the tip of a hand. 12 o'clock is up, sweeping clockwise."""
    angle = 2 * math.pi * (value / total)
    x = CX + length * math.sin(angle)
    y = CY - length * math.cos(angle)
    return x, y


def draw_static(draw, ox=0, oy=0):
    """Clock face: outer circle, tick marks, center hub. Black."""
    draw.ellipse(
        [CX - RADIUS - ox, CY - RADIUS - oy, CX + RADIUS - ox, CY + RADIUS - oy],
        outline=0, width=4,
    )
    for i in range(12):
        angle = 2 * math.pi * (i / 12)
        outer = RADIUS - 6
        inner = RADIUS - (22 if i % 3 == 0 else 12)  # longer ticks at 12/3/6/9
        x1 = CX + outer * math.sin(angle) - ox
        y1 = CY - outer * math.cos(angle) - oy
        x2 = CX + inner * math.sin(angle) - ox
        y2 = CY - inner * math.cos(angle) - oy
        draw.line([x1, y1, x2, y2], fill=0, width=3 if i % 3 == 0 else 2)
    draw.ellipse(
        [CX - HUB_R - ox, CY - HUB_R - oy, CX + HUB_R - ox, CY + HUB_R - oy],
        fill=0,
    )


def draw_hour_hand(draw, hour, minute, fill=0, ox=0, oy=0):
    """Hour hand. Advances smoothly with the minutes."""
    value = (hour % 12) + minute / 60.0
    x, y = hand_endpoint(HOUR_LEN, value, 12)
    draw.line([CX - ox, CY - oy, x - ox, y - oy], fill=fill, width=8)


def draw_minute_hand(draw, minute, fill=0, ox=0, oy=0):
    """Minute hand."""
    x, y = hand_endpoint(MIN_LEN, minute, 60)
    draw.line([CX - ox, CY - oy, x - ox, y - oy], fill=fill, width=5)


def to_buffer(image):
    """Convert a mode-'1' image to an e-paper buffer for display_Partial.

    Unlike display() (which inverts the black bytes itself at
    epd7in5b_V2.py:209), display_Partial sends the buffer to RAM as-is. So the
    bytes must already be in hardware polarity: 1=white, 0=black -- which is
    exactly what PIL's mode-'1' tobytes() gives (white bit=1, black bit=0).
    No inversion here."""
    return bytearray(image.convert("1").tobytes("raw"))


def full_refresh(epd, now):
    """Full refresh: static + black minute hand + RED hour hand."""
    logging.info("Full refresh")
    epd.init()

    black = Image.new("1", (epd.width, epd.height), 255)
    db = ImageDraw.Draw(black)
    draw_static(db)
    draw_minute_hand(db, now.minute, fill=0)

    red = Image.new("1", (epd.width, epd.height), 255)
    dr = ImageDraw.Draw(red)
    draw_hour_hand(dr, now.hour, now.minute, fill=0)

    epd.display(epd.getbuffer(black), epd.getbuffer(red))


def partial_refresh(epd, now):
    """Black-only partial refresh of the clock face: redraw static + both
    hands in black so the old minute hand is erased and the new one drawn.
    The red hour hand from the last full refresh lingers until the next one."""
    logging.info("Partial refresh - minute changed")
    epd.init_part()
    epd.partFlag = 1

    pad = 12
    x0 = CX - RADIUS - pad
    y0 = CY - RADIUS - pad
    x1 = CX + RADIUS + pad
    y1 = CY + RADIUS + pad

    # display_Partial needs the X range aligned to 8-pixel (byte) boundaries.
    region_x = (x0 // 8) * 8
    region_w = (((x1 - region_x) + 7) // 8) * 8
    region_y = y0
    region_h = y1 - y0

    region = Image.new("1", (region_w, region_h), 255)
    d = ImageDraw.Draw(region)
    draw_static(d, ox=region_x, oy=region_y)
    draw_hour_hand(d, now.hour, now.minute, fill=0, ox=region_x, oy=region_y)
    draw_minute_hand(d, now.minute, fill=0, ox=region_x, oy=region_y)

    epd.display_Partial(
        to_buffer(region),
        region_x, region_y, region_x + region_w, region_y + region_h,
    )


def clock():
    try:
        epd = epd7in5b_V2.EPD()
        logging.info("init and Clear")
        epd.init()
        epd.Clear()

        last_minute = -1
        last_hour = -1
        force_full = True

        while True:
            now = datetime.now()

            if now.minute == last_minute:
                time.sleep(1)
                continue

            do_full = (
                force_full
                or now.hour != last_hour
                or now.minute % FULL_REFRESH_MIN == 0
            )

            if do_full:
                full_refresh(epd, now)
            else:
                partial_refresh(epd, now)

            last_minute = now.minute
            last_hour = now.hour
            force_full = False

            epd.sleep()

            seconds_left = 60 - datetime.now().second
            time.sleep(seconds_left)

    except IOError as e:
        logging.info(e)

    except KeyboardInterrupt:
        logging.info("ctrl + c:")
        epd7in5b_V2.epdconfig.module_exit(cleanup=True)


if __name__ == "__main__":
    clock()
