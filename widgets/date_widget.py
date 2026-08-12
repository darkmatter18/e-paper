"""Date widget - displays day of week and full date."""
import os

from PIL import ImageDraw, ImageFont

from utils.datetime_util import DateTimeUtil
from widgets.widget import Widget, WidgetRegion

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Fonts
FONT_DATE_DAY = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Geomini-VariableFont_wght.ttf"), 60
)
FONT_DATE_NUM = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "HennyPenny-Regular.ttf"), 72
)
FONT_DATE_MY = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Geomini-VariableFont_wght.ttf"), 44
)


class DateWidget(Widget):
    """Displays date in bottom-left quadrant (400x240)."""

    def __init__(self):
        super().__init__(WidgetRegion(x=0, y=240, width=400, height=240))

    def draw(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None = None, **kwargs):
        """Draw date information.

        Args:
            black_draw: PIL ImageDraw for black channel
            red_draw: Optional PIL ImageDraw for red channel
            **kwargs: Must include 'now' (datetime object)
        """
        now = DateTimeUtil.now()

        qy = self.region.y

        # Day of week (e.g., "MONDAY")
        day_str = now.strftime("%A").upper()
        bbox = black_draw.textbbox((0, 0), day_str, font=FONT_DATE_DAY)
        tw = bbox[2] - bbox[0]
        black_draw.text(((400 - tw) // 2, qy + 70), day_str, font=FONT_DATE_DAY, fill=0)

        # Full date (e.g., "12 AUGUST 2026") - split into three parts
        day_num = now.strftime("%d")
        month_year = now.strftime("%B %Y").upper()

        # Measure total width
        bbox_day = black_draw.textbbox((0, 0), day_num, font=FONT_DATE_NUM)
        bbox_my = black_draw.textbbox((0, 0), month_year, font=FONT_DATE_MY)
        total_w = (bbox_day[2] - bbox_day[0]) + 10 + (bbox_my[2] - bbox_my[0])

        # Center the date
        start_x = (400 - total_w) // 2
        y_date = qy + 145

        # Draw day number in red if red_draw provided, otherwise black
        if red_draw:
            red_draw.text((start_x, y_date), day_num, font=FONT_DATE_NUM, fill=0)
        else:
            black_draw.text((start_x, y_date), day_num, font=FONT_DATE_NUM, fill=0)

        # Draw month and year in black
        x_my = start_x + (bbox_day[2] - bbox_day[0]) + 10
        black_draw.text((x_my, y_date + 10), month_year, font=FONT_DATE_MY, fill=0)

    def draw_decorations(self, black_draw: ImageDraw.ImageDraw):
        """Draw black decorative elements."""
        qx, qy, qw = self.region.x, self.region.y, self.region.width

        # Scalloped top border (start from 10 to avoid edge overflow)
        for i in range(10, qw - 20, 30):
            black_draw.arc([qx + i, qy + 8, qx + i + 26, qy + 28], 0, 180, fill=0, width=2)

        # Scalloped bottom border (start from 10 to avoid edge overflow)
        for i in range(10, qw - 20, 30):
            black_draw.arc([qx + i, 480 - 28, qx + i + 26, 480 - 8], 180, 360, fill=0, width=2)

        # Small diamond separators flanking the date text
        for dx in [60, 340]:
            dy = qy + 150
            black_draw.polygon([dx, dy - 4, dx + 4, dy, dx, dy + 4, dx - 4, dy], fill=0)

        # Dotted horizontal rules above and below text area
        for y in [qy + 55, qy + 200]:
            for x in range(30, 370, 8):
                black_draw.ellipse([x, y, x + 2, y + 2], fill=0)

    def draw_red_decorations(self, red_draw: ImageDraw.ImageDraw):
        """Draw red decorative elements."""
        qy = self.region.y

        # Red hearts flanking the weekday
        for hx in [35, 355]:
            hy = qy + 82
            red_draw.ellipse([hx - 6, hy - 6, hx, hy], fill=0)
            red_draw.ellipse([hx, hy - 6, hx + 6, hy], fill=0)
            red_draw.polygon([hx - 7, hy - 2, hx, hy + 6, hx + 7, hy - 2], fill=0)

        # Red accent stars at bottom corners
        for sx in [30, 370]:
            sy = 460
            self._draw_star(red_draw, sx, sy, 5, 2.5)

    def _draw_star(self, draw: ImageDraw.ImageDraw, cx: float, cy: float, outer_r: float, inner_r: float, points: int = 5):
        """Draw a star shape."""
        import math
        coords = []
        for i in range(points * 2):
            angle = math.pi * (i / points) - math.pi / 2
            r = outer_r if i % 2 == 0 else inner_r
            coords.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        draw.polygon(coords, fill=0)
