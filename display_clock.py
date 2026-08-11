import logging
import math
import os
import time
from datetime import datetime

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

from lib.waveshare_epd import epd7in5b_V2
from services.quote import ZenQuotesService
from services.weather import OpenWeatherMapService

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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

# How often to do a full (flashing) refresh. Red only renders on a full
# refresh, so this is when the red hour hand is redrawn.
# Between full refreshes the minute hand moves in black via partial refresh.
FULL_REFRESH_MIN = 15

FONT_DATE_DAY = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Geomini-VariableFont_wght.ttf"), 60
)
FONT_DATE_NUM = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "HennyPenny-Regular.ttf"), 72
)

FONT_DATE_MY = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Geomini-VariableFont_wght.ttf"), 44
)

FONT_DIGI = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Geomini-VariableFont_wght.ttf"), 52
)

FONT_DIGI_SM = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Geomini-VariableFont_wght.ttf"), 36
)

FONT_QUOTE_TEXT = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Geomini-VariableFont_wght.ttf"), 32
)

FONT_QUOTE_AUTHOR = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Geomini-VariableFont_wght.ttf"), 24
)

FONT_WEATHER_TEMP = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Geomini-VariableFont_wght.ttf"), 28
)

FONT_WEATHER_DAY = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Geomini-VariableFont_wght.ttf"), 18
)

FONT_WEATHER_LABEL = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Geomini-VariableFont_wght.ttf"), 22
)

FONT_WEATHER_SMALL = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Geomini-VariableFont_wght.ttf"), 14
)


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



def draw_digital(draw, now, ox=0, oy=0, red_draw=None):
    """Draw HH / MM / AM|PM stacked vertically in the right half of upper-left.
    Hour is drawn on red_draw (red channel) if provided."""
    hour_12 = now.hour % 12 or 12
    ampm = "AM" if now.hour < 12 else "PM"

    line_spacing = 65
    total_h = 3 * line_spacing - (line_spacing - 52)
    y_start = (240 - total_h) // 2

    lines = [
        (f"{hour_12:02d}", FONT_DIGI, red_draw or draw),
        (f"{now.minute:02d}", FONT_DIGI, draw),
        (ampm, FONT_DIGI_SM, draw),
    ]

    y = y_start - oy
    for text, font, target in lines:
        bbox = target.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = DIGI_X + (120 - tw) // 2 - ox
        target.text((x, y), text, font=font, fill=0)
        y += line_spacing


def draw_decorations(draw, ox=0, oy=0):
    """Artistic touches around the upper-left quadrant."""
    # Dot ring around the analog clock
    for i in range(60):
        angle = 2 * math.pi * (i / 60)
        r = RADIUS + 8
        x = CX + r * math.sin(angle) - ox
        y = CY - r * math.cos(angle) - oy
        if i % 5 == 0:
            draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=0)
        else:
            draw.point((x, y), fill=0)

    # Small separator dots between digital lines
    dot_x = DIGI_X + 60 - ox
    line_spacing = 65
    total_h = 3 * line_spacing - (line_spacing - 52)
    y_start = (240 - total_h) // 2
    for i in range(2):
        dot_y = y_start + 52 + i * line_spacing + 4 - oy
        draw.ellipse([dot_x - 3, dot_y, dot_x + 3, dot_y + 6], fill=0)

    # Corner flourishes in upper-left quadrant — L-shaped brackets
    for cx, cy, sx, sy in [(8, 8, 1, 1), (392, 8, -1, 1), (8, 232, 1, -1), (392, 232, -1, -1)]:
        cx -= ox
        cy -= oy
        draw.line([cx, cy, cx + sx * 20, cy], fill=0, width=2)
        draw.line([cx, cy, cx, cy + sy * 20], fill=0, width=2)

    # Ornamental brackets flanking the digital time
    bx_l = DIGI_X - 20 - ox
    bx_r = DIGI_X + 140 - ox
    bt = y_start + 5 - oy
    bb = y_start + total_h - 5 - oy
    draw.arc([bx_l - 5, bt, bx_l + 15, bb], 90, 270, fill=0, width=2)
    draw.arc([bx_r - 15, bt, bx_r + 5, bb], 270, 90, fill=0, width=2)

    # Sun/moon indicator based on hour (drawn near top-center of quadrant)
    icon_x = 200 - ox
    icon_y = 16 - oy
    now_h = datetime.now().hour
    if 6 <= now_h < 18:
        # Sun — circle with rays
        draw.ellipse([icon_x - 6, icon_y - 6, icon_x + 6, icon_y + 6], outline=0, width=2)
        for i in range(8):
            a = 2 * math.pi * (i / 8)
            draw.line([
                icon_x + 9 * math.cos(a), icon_y + 9 * math.sin(a),
                icon_x + 13 * math.cos(a), icon_y + 13 * math.sin(a),
            ], fill=0, width=1)
    else:
        # Moon — crescent
        draw.ellipse([icon_x - 8, icon_y - 8, icon_x + 8, icon_y + 8], fill=0)
        draw.ellipse([icon_x - 3, icon_y - 8, icon_x + 11, icon_y + 8], fill=255)


def _draw_star(draw, cx, cy, outer_r, inner_r, points=5):
    """Draw a small filled star."""
    coords = []
    for i in range(points * 2):
        r = outer_r if i % 2 == 0 else inner_r
        angle = math.pi * i / points - math.pi / 2
        coords.append(cx + r * math.cos(angle))
        coords.append(cy + r * math.sin(angle))
    draw.polygon(coords, fill=0)


def draw_red_decorations(draw, ox=0, oy=0):
    """Red accent elements for the upper-left quadrant."""
    # Small red diamond below the analog clock
    dx, dy = CX - ox, CY + RADIUS + 14 - oy
    draw.polygon([dx, dy - 5, dx + 5, dy, dx, dy + 5, dx - 5, dy], fill=0)

    # Red accent line flanking the digital area
    lx = DIGI_X - 12 - ox
    draw.line([lx, 50 - oy, lx, 190 - oy], fill=0, width=2)

    # Red dots at the quarter-hour positions on the outer ring
    for i in [0, 15, 30, 45]:
        angle = 2 * math.pi * (i / 60)
        r = RADIUS + 8
        x = CX + r * math.sin(angle) - ox
        y = CY - r * math.cos(angle) - oy
        draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=0)

    # Small red stars at top corners of upper-left quadrant
    for sx, sy in [(25 - ox, 22 - oy), (375 - ox, 22 - oy)]:
        _draw_star(draw, sx, sy, 6, 3)


def draw_date_decorations(draw):
    """Black decorations for the bottom-left date quadrant."""
    qx, qy, qw = 0, 240, 400

    # Scalloped top border
    for i in range(0, qw, 30):
        draw.arc([qx + i + 2, qy + 8, qx + i + 28, qy + 28], 0, 180, fill=0, width=2)

    # Scalloped bottom border
    for i in range(0, qw, 30):
        draw.arc([qx + i + 2, 480 - 28, qx + i + 28, 480 - 8], 180, 360, fill=0, width=2)

    # Small diamond separators flanking the date text
    for dx in [60, 340]:
        dy = qy + 150
        draw.polygon([dx, dy - 4, dx + 4, dy, dx, dy + 4, dx - 4, dy], fill=0)

    # Dotted horizontal rules above and below text area
    for y in [qy + 55, qy + 200]:
        for x in range(30, 370, 8):
            draw.ellipse([x, y, x + 2, y + 2], fill=0)


def draw_date_red_decorations(draw):
    """Red decorations for the bottom-left date quadrant."""
    qy = 240

    # Red hearts flanking the weekday
    for hx in [35, 355]:
        hy = qy + 82
        draw.ellipse([hx - 6, hy - 6, hx, hy], fill=0)
        draw.ellipse([hx, hy - 6, hx + 6, hy], fill=0)
        draw.polygon([hx - 6, hy - 2, hx, hy + 7, hx + 6, hy - 2], fill=0)

    # Red corner dots in bottom-left quadrant
    for cx, cy in [(15, 255), (385, 255), (15, 465), (385, 465)]:
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=0)


def draw_date(draw, now, red_draw=None):
    """Draw date in the bottom-left quadrant (0,240)-(400,480).
    Layout: day-of-week on one line, full date on the next."""
    qx, qy, qw = 0, 240, 400

    day_name = now.strftime("%A")
    date_str = now.strftime("%d %B %Y")

    # Day of week (centered)
    bbox = draw.textbbox((0, 0), day_name, font=FONT_DATE_DAY)
    tw = bbox[2] - bbox[0]
    draw.text(((qw - tw) // 2 + qx, qy + 70), day_name, font=FONT_DATE_DAY, fill=0)

    # Full date (red if red_draw provided)
    target = red_draw or draw
    bbox = target.textbbox((0, 0), date_str, font=FONT_DATE_MY)
    tw = bbox[2] - bbox[0]
    target.text(((qw - tw) // 2 + qx, qy + 130), date_str, font=FONT_DATE_MY, fill=0)


def draw_dividers(draw):
    """Draw the layout divider lines: vertical center, horizontal left-half."""
    draw.line([400, 0, 400, 480], fill=0, width=2)
    draw.line([0, 240, 400, 240], fill=0, width=2)


def wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def draw_weather_icon(draw, icon_code, cx, cy):
    """Draw simplified weather icon based on OpenWeatherMap icon code."""
    # Icon codes: 01d/01n=clear, 02d/02n=few clouds, 03d/03n=clouds,
    #             04d/04n=broken clouds, 09d/09n=rain, 10d/10n=rain,
    #             11d/11n=thunderstorm, 13d/13n=snow, 50d/50n=mist

    icon_base = icon_code[:2] if len(icon_code) >= 2 else "01"

    if icon_base == "01":  # Clear sky - sun
        draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], outline=0, width=2)
        for i in range(8):
            angle = 2 * math.pi * i / 8
            x1 = cx + 12 * math.cos(angle)
            y1 = cy + 12 * math.sin(angle)
            x2 = cx + 16 * math.cos(angle)
            y2 = cy + 16 * math.sin(angle)
            draw.line([x1, y1, x2, y2], fill=0, width=2)
    elif icon_base in ["02", "03", "04"]:  # Clouds
        draw.ellipse([cx - 12, cy - 6, cx - 2, cy + 4], fill=0)
        draw.ellipse([cx - 6, cy - 8, cx + 6, cy + 2], fill=0)
        draw.ellipse([cx + 2, cy - 6, cx + 12, cy + 4], fill=0)
    elif icon_base in ["09", "10"]:  # Rain
        draw.ellipse([cx - 10, cy - 8, cx + 10, cy], fill=0)
        for i in range(3):
            x = cx - 6 + i * 6
            draw.line([x, cy + 2, x, cy + 10], fill=0, width=2)
    elif icon_base == "11":  # Thunderstorm
        draw.ellipse([cx - 10, cy - 8, cx + 10, cy], fill=0)
        draw.polygon([cx, cy + 2, cx - 6, cy + 8, cx - 2, cy + 8,
                     cx - 4, cy + 12, cx + 4, cy + 4, cx, cy + 4], fill=0)
    elif icon_base == "13":  # Snow
        for i in range(6):
            angle = math.pi * i / 3
            x1 = cx + 10 * math.cos(angle)
            y1 = cy + 10 * math.sin(angle)
            draw.line([cx, cy, x1, y1], fill=0, width=2)
        draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=0)
    else:  # Mist/fog
        for i in range(3):
            y = cy - 6 + i * 6
            draw.line([cx - 10, y, cx + 10, y], fill=0, width=2)


def draw_weather(draw, weather_data):
    """Draw weather forecast in top part of right panel (400,0)-(800,240)."""
    qx, qy, qw = 400, 0, 400
    weather_h = 240

    # Current weather in single line: Temp | Description | Rain% | Icon
    current = weather_data.current

    # Layout elements horizontally
    y_line = qy + 25

    # Temperature (start from left)
    temp_text = f"{int(current.temperature)}°"
    temp_x = qx + 30
    draw.text((temp_x, y_line - 10), temp_text, font=FONT_WEATHER_TEMP, fill=0)

    # Description
    desc_text = current.description.title()
    bbox = draw.textbbox((0, 0), desc_text, font=FONT_WEATHER_DAY)
    desc_x = temp_x + 55
    draw.text((desc_x, y_line - 6), desc_text, font=FONT_WEATHER_DAY, fill=0)
    desc_w = bbox[2] - bbox[0]

    # Rain probability if > 0
    rain_x = desc_x + desc_w + 15
    if current.rain_probability > 0:
        rain_text = f"{current.rain_probability}%"
        draw.text((rain_x, y_line - 6), rain_text, font=FONT_WEATHER_DAY, fill=0)
        # Droplet icon
        bbox = draw.textbbox((0, 0), rain_text, font=FONT_WEATHER_DAY)
        drop_x = rain_x + (bbox[2] - bbox[0]) + 4
        drop_y = y_line - 4
        draw.ellipse([drop_x, drop_y, drop_x + 5, drop_y + 8], fill=0)
        # Weather icon on the right after rain
        icon_x = drop_x + 15
    else:
        # Weather icon right after description if no rain
        icon_x = rain_x

    # Draw icon aligned with text (adjusted y position)
    icon_y = y_line + 4  # Align with text baseline
    draw_weather_icon(draw, current.icon, icon_x, icon_y)

    # Separator line
    sep_y = qy + 55
    draw.line([qx + 20, sep_y, qx + qw - 20, sep_y], fill=0, width=1)

    # 5-day forecast bars
    forecast = weather_data.forecast[:5]
    if not forecast:
        return

    bar_y = qy + 110  # Start below separator line
    bar_h = 55  # Bar area height
    bar_w = 24  # Narrow but not too thin

    # Distribute evenly across the full width with margins
    margin = 30  # Left/right margins
    available_width = qw - 2 * margin
    total_bar_width = len(forecast) * bar_w
    total_gap_width = available_width - total_bar_width
    bar_spacing = total_gap_width // (len(forecast) + 1)  # Even spacing

    start_x = qx + margin + bar_spacing  # Start with margin + first gap

    # Get temp range for scaling
    all_temps = []
    for day in forecast:
        all_temps.extend([day.temp_min, day.temp_max])
    temp_min = min(all_temps)
    temp_max = max(all_temps)
    temp_range = temp_max - temp_min if temp_max > temp_min else 10

    for i, day in enumerate(forecast):
        x = start_x + i * (bar_w + bar_spacing)
        center_x = x + bar_w // 2

        # Calculate bar heights
        max_h = int((day.temp_max - temp_min) / temp_range * bar_h)
        min_h = int((day.temp_min - temp_min) / temp_range * bar_h)

        # Draw bar (min to max range) - outline only
        bar_top = bar_y + bar_h - max_h
        bar_bot = bar_y + bar_h - min_h
        draw.rectangle([x, bar_top, x + bar_w, bar_bot], outline=0, width=2)

        # Weather icon above bar
        icon_y = bar_top - 35
        draw_weather_icon(draw, day.icon, center_x, icon_y)

        # Max temp label above bar
        max_temp = f"{int(day.temp_max)}°"
        bbox = draw.textbbox((0, 0), max_temp, font=FONT_WEATHER_SMALL)
        tw = bbox[2] - bbox[0]
        draw.text((center_x - tw // 2, bar_top - 16), max_temp, font=FONT_WEATHER_SMALL, fill=0)

        # Min temp label - fixed position below bar area to avoid overlap
        min_temp = f"{int(day.temp_min)}°"
        bbox = draw.textbbox((0, 0), min_temp, font=FONT_WEATHER_SMALL)
        tw = bbox[2] - bbox[0]
        min_y = bar_y + bar_h + 2  # Fixed position below bar area
        draw.text((center_x - tw // 2, min_y), min_temp, font=FONT_WEATHER_SMALL, fill=0)

        # Rain probability if > 0 - positioned below min temp
        if day.rain_probability > 0:
            rain_text = f"{day.rain_probability}%"
            bbox = draw.textbbox((0, 0), rain_text, font=FONT_WEATHER_SMALL)
            tw = bbox[2] - bbox[0]
            rain_y = min_y + 16  # Below min temp
            draw.text((center_x - tw // 2, rain_y), rain_text, font=FONT_WEATHER_SMALL, fill=0)
            # Small droplet icon next to percentage
            drop_x = center_x + tw // 2 + 3
            drop_y = rain_y + 2
            draw.ellipse([drop_x, drop_y, drop_x + 4, drop_y + 6], fill=0)

        # Day label at bottom
        day_name = datetime.strptime(day.date, "%Y-%m-%d").strftime("%a")
        bbox = draw.textbbox((0, 0), day_name, font=FONT_WEATHER_DAY)
        tw = bbox[2] - bbox[0]
        # Position depends on whether rain is shown
        label_y = min_y + 32 if day.rain_probability > 0 else min_y + 16
        draw.text((center_x - tw // 2, label_y), day_name, font=FONT_WEATHER_DAY, fill=0)


def draw_quote(draw, quote_text, quote_author):
    """Draw quote in bottom part of right panel (400,240)-(800,480)."""
    qx, qy, qw, qh = 400, 240, 400, 240
    padding = 30

    # Opening quote mark (large decorative)
    draw.text((qx + padding - 8, qy + 20), "“", font=FONT_QUOTE_TEXT, fill=0)

    # Wrap and draw quote text
    wrapped = wrap_text(quote_text, FONT_QUOTE_TEXT, qw - 2 * padding, draw)
    y = qy + 60
    for line in wrapped:
        bbox = draw.textbbox((0, 0), line, font=FONT_QUOTE_TEXT)
        tw = bbox[2] - bbox[0]
        x = qx + (qw - tw) // 2
        draw.text((x, y), line, font=FONT_QUOTE_TEXT, fill=0)
        y += 40

    # Closing quote mark
    bbox = draw.textbbox((0, 0), "”", font=FONT_QUOTE_TEXT)
    qm_w = bbox[2] - bbox[0]
    draw.text((qx + qw - padding - qm_w + 8, y - 20), "”", font=FONT_QUOTE_TEXT, fill=0)

    # Author name (centered at bottom)
    author_text = f"— {quote_author}"
    bbox = draw.textbbox((0, 0), author_text, font=FONT_QUOTE_AUTHOR)
    tw = bbox[2] - bbox[0]
    draw.text((qx + (qw - tw) // 2, qy + qh - 50), author_text, font=FONT_QUOTE_AUTHOR, fill=0)

def draw_weather_decorations(draw):
    """Black decorations for weather panel (top of right side)."""
    qx, qy, qw = 400, 0, 400

    # Horizontal separator line
    draw.line([qx + 20, 240, qx + qw - 20, 240], fill=0, width=2)

    # Corner brackets for weather section
    for cx, cy, sx, sy in [
        (qx + 15, qy + 15, 1, 1),
        (qx + qw - 15, qy + 15, -1, 1),
    ]:
        draw.line([cx, cy, cx + sx * 20, cy], fill=0, width=2)
        draw.line([cx, cy, cx, cy + sy * 20], fill=0, width=2)


def draw_quote_decorations(draw):
    """Black decorations for quote panel (bottom of right side)."""
    qx, qy, qw, qh = 400, 240, 400, 240

    # Corner brackets for quote section
    for cx, cy, sx, sy in [
        (qx + 15, qy + qh - 15, 1, -1),
        (qx + qw - 15, qy + qh - 15, -1, -1),
    ]:
        draw.line([cx, cy, cx + sx * 20, cy], fill=0, width=2)
        draw.line([cx, cy, cx, cy + sy * 20], fill=0, width=2)


def draw_weather_red_decorations(draw):
    """Red decorations for weather panel."""
    qx, qy, qw = 400, 0, 400

    # Small red dots at corners
    for cx, cy in [(qx + 35, qy + 35), (qx + qw - 35, qy + 35)]:
        draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=0)


def draw_quote_red_decorations(draw):
    """Red decorations for quote panel."""
    qx, qy = 400, 240

    # Small red hearts flanking quote
    for hx in [qx + 25, qx + 400 - 25]:
        hy = qy + 30
        draw.ellipse([hx - 3, hy - 3, hx, hy], fill=0)
        draw.ellipse([hx, hy - 3, hx + 3, hy], fill=0)
        draw.polygon([hx - 3, hy - 1, hx, hy + 4, hx + 3, hy - 1], fill=0)


def full_refresh(epd, now, quote_service, weather_service):
    """Full refresh: clock, date, weather, quote with decorations."""
    logger.info("Full refresh")
    epd.init()

    # Fetch data (services handle caching)
    quote = quote_service.get_quote_of_the_day()
    weather = weather_service.get_weather(
        lat=float(os.getenv("LATITUDE", "0")),
        lon=float(os.getenv("LONGITUDE", "0"))
    )

    black = Image.new("1", (epd.width, epd.height), 255)
    db = ImageDraw.Draw(black)
    draw_dividers(db)
    draw_static(db)
    draw_minute_hand(db, now.minute, fill=0)
    draw_decorations(db)

    draw_date(db, now)
    draw_date_decorations(db)

    draw_weather(db, weather)
    draw_weather_decorations(db)

    draw_quote(db, quote.text, quote.author)
    draw_quote_decorations(db)

    red = Image.new("1", (epd.width, epd.height), 255)
    dr = ImageDraw.Draw(red)
    draw_hour_hand(dr, now.hour, now.minute, fill=0)
    draw_digital(db, now, red_draw=dr)
    draw_red_decorations(dr)
    draw_date(db, now, red_draw=dr)
    draw_date_red_decorations(dr)
    draw_weather_red_decorations(dr)
    draw_quote_red_decorations(dr)

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
    draw_decorations(d, ox=region_x, oy=region_y)
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
        quote_service = ZenQuotesService()

        # Initialize weather service
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            logger.warning("OPENWEATHER_API_KEY not set, weather will show fallback data")
        weather_service = OpenWeatherMapService(api_key or "dummy")

        logger.info("init and Clear")
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
                full_refresh(epd, now, quote_service, weather_service)
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
        logger.info(e)

    except KeyboardInterrupt:
        logger.info("ctrl + c:")
        epd7in5b_V2.epdconfig.module_exit(cleanup=True)


if __name__ == "__main__":
    clock()
