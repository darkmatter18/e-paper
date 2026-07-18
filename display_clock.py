import logging
import math
import os
import time
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from lib.waveshare_epd import epd7in5b_V2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(level=logging.DEBUG)

# --- Layout: 800x480 split into regions ---
# Left half (400x480) split into upper (400x240) and lower (400x240).
# Right half (400x480) is one panel.
DISPLAY_W, DISPLAY_H = 800, 480

# --- Clock geometry (left half of upper-left quadrant: 200x240) ---
CX, CY = 100, 120  # center of the analog clock
RADIUS = 90  # outer circle radius
HOUR_LEN = 50  # hour hand length
MIN_LEN = 78  # minute hand length
HUB_R = 5  # center hub radius

# --- Digital clock position (right half of upper-left quadrant) ---
DIGI_X = 240  # left edge of digital text area
DIGI_Y_START = 40  # top of first line

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
        outline=0,
        width=4,
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


FONT_DIGI = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "HennyPenny-Regular.ttf"), 52
)


def draw_digital(draw, now, ox=0, oy=0):
    """Draw HH / MM / AM|PM stacked vertically in the right half of upper-left."""
    hour_12 = now.hour % 12 or 12
    ampm = "AM" if now.hour < 12 else "PM"
    lines = [f"{hour_12:02d}", f"{now.minute:02d}", ampm]

    y = DIGI_Y_START - oy
    for text in lines:
        bbox = draw.textbbox((0, 0), text, font=FONT_DIGI)
        tw = bbox[2] - bbox[0]
        x = DIGI_X + (120 - tw) // 2 - ox
        draw.text((x, y), text, font=FONT_DIGI, fill=0)
        y += 65


def draw_dividers(draw):
    """Draw the layout divider lines: vertical center, horizontal left-half."""
    draw.line([400, 0, 400, 480], fill=0, width=2)
    draw.line([0, 240, 400, 240], fill=0, width=2)


def full_refresh(epd, now):
    """Full refresh: analog + digital clock in upper-left, dividers, RED hour hand."""
    logging.info("Full refresh")
    epd.init()

    black = Image.new("1", (epd.width, epd.height), 255)
    db = ImageDraw.Draw(black)
    draw_dividers(db)
    draw_static(db)
    draw_minute_hand(db, now.minute, fill=0)
    draw_digital(db, now)

    red = Image.new("1", (epd.width, epd.height), 255)
    dr = ImageDraw.Draw(red)
    draw_hour_hand(dr, now.hour, now.minute, fill=0)

    epd.display(epd.getbuffer(black), epd.getbuffer(red))


def get_region_coords():
    """The entire upper-left quadrant (0,0)-(400,240), 8px aligned."""
    region_x = 0
    region_y = 0
    region_w = 400
    region_h = 240
    return region_x, region_y, region_w, region_h


def render_region(now, region_x, region_y, region_w, region_h):
    """Draw analog + digital clock into a partial-region image."""
    region = Image.new("1", (region_w, region_h), 255)
    d = ImageDraw.Draw(region)
    draw_static(d, ox=region_x, oy=region_y)
    draw_hour_hand(d, now.hour, now.minute, fill=0, ox=region_x, oy=region_y)
    draw_minute_hand(d, now.minute, fill=0, ox=region_x, oy=region_y)
    draw_digital(d, now, ox=region_x, oy=region_y)
    return region


def partial_refresh_with_old(
    epd, old_buf, new_buf, region_x, region_y, region_w, region_h
):
    """Partial refresh that sends the previous frame as the 'old' buffer so
    the controller knows which pixels to erase."""
    from lib.waveshare_epd import epdconfig

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

    epd.send_command(0x10)
    epd.send_data2(old_buf)

    epd.send_command(0x13)
    epd.send_data2(new_buf)

    epd.send_command(0x12)
    epdconfig.delay_ms(100)
    epd.ReadBusy()


def clock():
    try:
        epd = epd7in5b_V2.EPD()
        logging.info("init and Clear")
        epd.init()
        epd.Clear()

        region_x, region_y, region_w, region_h = get_region_coords()
        last_minute = -1
        last_hour = -1
        force_full = True
        prev_buf = None

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
                prev_buf = to_buffer(
                    render_region(now, region_x, region_y, region_w, region_h)
                )
            else:
                epd.init_part()
                new_region = render_region(now, region_x, region_y, region_w, region_h)
                new_buf = to_buffer(new_region)
                partial_refresh_with_old(
                    epd, prev_buf, new_buf, region_x, region_y, region_w, region_h
                )
                prev_buf = new_buf

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
