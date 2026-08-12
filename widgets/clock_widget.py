"""Clock widget - displays analog clock with digital time."""
import math
import os
from datetime import datetime

from PIL import ImageDraw, ImageFont

from utils import DateTimeUtil
from widgets.widget import Widget, WidgetRegion

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Clock geometry
CX, CY = 100, 120  # center of the analog clock
RADIUS = 90  # outer circle radius
HOUR_LEN = 50  # hour hand length
MIN_LEN = 78  # minute hand length
HUB_R = 5  # center hub radius

# Digital clock position
DIGI_X = 240  # left edge of digital text area

# Fonts
FONT_DIGI = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Geomini-VariableFont_wght.ttf"), 52
)
FONT_DIGI_SM = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Geomini-VariableFont_wght.ttf"), 36
)


class ClockWidget(Widget):
    """Displays analog clock with digital time in upper-left quadrant (400x240)."""

    def __init__(self):
        super().__init__(WidgetRegion(x=0, y=0, width=400, height=240))

    @property
    def supports_partial_refresh(self) -> bool:
        """Clock supports partial refresh for minute hand updates."""
        return True

    def draw(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None = None, **kwargs):
        """Draw clock face and hands.

        Args:
            black_draw: PIL ImageDraw for black channel
            red_draw: Optional PIL ImageDraw for red channel
            **kwargs: Must include 'now' (datetime object)
        """
        now = DateTimeUtil.now()

        # Draw static clock face
        self._draw_clock_face(black_draw)

        # Draw hands
        if red_draw:
            # Full refresh: draw hour hand in red
            self._draw_hour_hand(red_draw, now.hour, now.minute, fill=0)
        else:
            # Partial refresh: draw hour hand in black
            self._draw_hour_hand(black_draw, now.hour, now.minute, fill=0)

        self._draw_minute_hand(black_draw, now.minute, fill=0)

        # Draw digital time
        self._draw_digital(black_draw, now, red_draw=red_draw)

    def _draw_clock_face(self, draw: ImageDraw.ImageDraw):
        """Draw clock face: outer circle, tick marks, center hub."""
        # Outer circle
        draw.ellipse(
            [CX - RADIUS, CY - RADIUS, CX + RADIUS, CY + RADIUS],
            outline=0,
            width=4,
        )

        # Tick marks
        for i in range(12):
            angle = 2 * math.pi * (i / 12)
            outer = RADIUS - 6
            inner = RADIUS - (22 if i % 3 == 0 else 12)  # longer ticks at 12/3/6/9
            x1 = CX + outer * math.sin(angle)
            y1 = CY - outer * math.cos(angle)
            x2 = CX + inner * math.sin(angle)
            y2 = CY - inner * math.cos(angle)
            draw.line([x1, y1, x2, y2], fill=0, width=3 if i % 3 == 0 else 2)

        # Center hub
        draw.ellipse([CX - HUB_R, CY - HUB_R, CX + HUB_R, CY + HUB_R], fill=0)

    def _draw_hour_hand(self, draw: ImageDraw.ImageDraw, hour: int, minute: int, fill: int):
        """Draw hour hand (advances smoothly with minutes)."""
        value = (hour % 12) + minute / 60.0
        angle = 2 * math.pi * (value / 12)
        x = CX + HOUR_LEN * math.sin(angle)
        y = CY - HOUR_LEN * math.cos(angle)
        draw.line([CX, CY, x, y], fill=fill, width=8)

    def _draw_minute_hand(self, draw: ImageDraw.ImageDraw, minute: int, fill: int):
        """Draw minute hand."""
        angle = 2 * math.pi * (minute / 60)
        x = CX + MIN_LEN * math.sin(angle)
        y = CY - MIN_LEN * math.cos(angle)
        draw.line([CX, CY, x, y], fill=fill, width=5)

    def _draw_digital(self, draw: ImageDraw.ImageDraw, now: datetime, red_draw: ImageDraw.ImageDraw | None = None):
        """Draw digital time (HH / MM / AM|PM stacked vertically)."""
        hour_12 = now.hour % 12 or 12
        ampm = "AM" if now.hour < 12 else "PM"

        line_spacing = 65
        total_h = 3 * line_spacing - (line_spacing - 52)
        y_start = (self.region.height - total_h) // 2

        lines = [
            (f"{hour_12:02d}", FONT_DIGI, red_draw or draw),  # Hour in red if available
            (f"{now.minute:02d}", FONT_DIGI, draw),
            (ampm, FONT_DIGI_SM, draw),
        ]

        y = y_start
        for text, font, target in lines:
            bbox = target.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            x = DIGI_X + (120 - tw) // 2
            target.text((x, y), text, font=font, fill=0)
            y += line_spacing

    def draw_decorations(self, black_draw: ImageDraw.ImageDraw):
        """Draw black decorative elements."""
        # Dot ring around the analog clock
        for i in range(60):
            angle = 2 * math.pi * (i / 60)
            r = RADIUS + 8
            x = CX + r * math.sin(angle)
            y = CY - r * math.cos(angle)
            if i % 5 == 0:
                black_draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=0)
            else:
                black_draw.point((x, y), fill=0)

        # Small separator dots between digital lines
        dot_x = DIGI_X + 60
        line_spacing = 65
        total_h = 3 * line_spacing - (line_spacing - 52)
        y_start = (self.region.height - total_h) // 2
        for i in range(2):
            dot_y = y_start + 52 + i * line_spacing + 4
            black_draw.ellipse([dot_x - 3, dot_y, dot_x + 3, dot_y + 6], fill=0)

        # Corner flourishes (L-shaped brackets)
        for cx, cy, sx, sy in [(8, 8, 1, 1), (392, 8, -1, 1), (8, 232, 1, -1), (392, 232, -1, -1)]:
            black_draw.line([cx, cy, cx + sx * 20, cy], fill=0, width=2)
            black_draw.line([cx, cy, cx, cy + sy * 20], fill=0, width=2)

        # Ornamental brackets flanking the digital time
        bx_l = DIGI_X - 20
        bx_r = DIGI_X + 140
        bt = y_start + 5
        bb = y_start + total_h - 5
        black_draw.arc([bx_l - 5, bt, bx_l + 15, bb], 90, 270, fill=0, width=2)
        black_draw.arc([bx_r - 15, bt, bx_r + 5, bb], 270, 90, fill=0, width=2)

        # Sun/moon indicator based on hour
        icon_x = 200
        icon_y = 16
        now_h = DateTimeUtil.now().hour
        if 6 <= now_h < 18:
            # Sun — circle with rays
            black_draw.ellipse([icon_x - 6, icon_y - 6, icon_x + 6, icon_y + 6], outline=0, width=2)
            for i in range(8):
                a = 2 * math.pi * (i / 8)
                black_draw.line([
                    icon_x + 9 * math.cos(a), icon_y + 9 * math.sin(a),
                    icon_x + 13 * math.cos(a), icon_y + 13 * math.sin(a),
                ], fill=0, width=1)
        else:
            # Moon — crescent
            black_draw.ellipse([icon_x - 8, icon_y - 8, icon_x + 8, icon_y + 8], fill=0)
            black_draw.ellipse([icon_x - 3, icon_y - 8, icon_x + 11, icon_y + 8], fill=255)

    def draw_red_decorations(self, red_draw: ImageDraw.ImageDraw):
        """Draw red decorative elements."""
        # Small red diamond below the analog clock
        dx, dy = CX, CY + RADIUS + 14
        red_draw.polygon([dx, dy - 5, dx + 5, dy, dx, dy + 5, dx - 5, dy], fill=0)

        # Red dots at the quarter-hour positions on the outer ring
        for i in [0, 15, 30, 45]:
            angle = 2 * math.pi * (i / 60)
            r = RADIUS + 8
            x = CX + r * math.sin(angle)
            y = CY - r * math.cos(angle)
            red_draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=0)

        # Small red stars at top corners
        for sx, sy in [(25, 22), (375, 22)]:
            self._draw_star(red_draw, sx, sy, 6, 3)

    def _draw_star(self, draw: ImageDraw.ImageDraw, cx: float, cy: float, outer_r: float, inner_r: float, points: int = 5):
        """Draw a star shape."""
        coords = []
        for i in range(points * 2):
            angle = math.pi * (i / points) - math.pi / 2
            r = outer_r if i % 2 == 0 else inner_r
            coords.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        draw.polygon(coords, fill=0)
