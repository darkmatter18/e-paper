"""Date widget - displays day of week and full date.

This module implements a decorative date display widget showing both the day of
the week and the full calendar date. Designed for the bottom-left quadrant
(400x240) of the 800x480 e-paper display.

Features:
    - Large, centered weekday name (e.g., "MONDAY")
    - Mixed-font date display: decorative day number + clean month/year
    - Day number emphasized in red during full refresh
    - Ornamental scalloped borders, dots, diamonds, and heart accents

Typography:
    - Weekday: Geomini 60pt (bold, geometric sans-serif)
    - Day number: Henny Penny 72pt (decorative serif, emphasized)
    - Month/Year: Geomini 44pt (clean, readable sans-serif)

Color Usage:
    - Black: Weekday, month/year, decorative borders
    - Red: Day number, heart accents, corner stars

Layout:
    The widget uses a two-tier layout with decorative borders:
    - Top tier (70px): Weekday centered with heart accents
    - Bottom tier (145px): Date with diamond separators
    - Scalloped borders at top and bottom edges
"""
import os

from PIL import ImageDraw, ImageFont

from utils.datetime_util import DateTimeUtil
from widgets.widget import Widget, WidgetRegion

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Date display fonts
FONT_DATE_DAY = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Geomini-VariableFont_wght.ttf"), 60
)  # Weekday font (large, bold sans-serif)

FONT_DATE_NUM = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "HennyPenny-Regular.ttf"), 72
)  # Day number font (decorative serif, emphasized)

FONT_DATE_MY = ImageFont.truetype(
    os.path.join(BASE_DIR, "fonts", "Geomini-VariableFont_wght.ttf"), 44
)  # Month and year font (readable sans-serif)


class DateWidget(Widget):
    """Displays date in bottom-left quadrant (400x240).

    Shows current date in a decorative two-tier layout:
    - Upper section: Day of week (e.g., "MONDAY") with heart accents
    - Lower section: Full date (e.g., "12 AUGUST 2026") with mixed fonts

    Design Philosophy:
        The date widget uses decorative typography and ornamental elements to create
        a vintage calendar aesthetic. The day number is emphasized in red and uses
        a distinctive decorative font (Henny Penny) to draw attention.

    Refresh Behavior:
        Updates only during full refresh (daily or on-demand). Date changes are
        infrequent enough that partial refresh support is unnecessary.

    Attributes:
        region: WidgetRegion(x=0, y=240, width=400, height=240) - bottom-left quadrant
    """

    def __init__(self):
        """Initialize date widget with bottom-left quadrant region."""
        super().__init__(WidgetRegion(x=0, y=240, width=400, height=240))

    def draw(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None = None, **kwargs):
        """Draw date information in two-tier layout.

        Renders weekday and full date with mixed fonts for visual hierarchy.
        Day number is drawn in red when available to create emphasis and visual
        interest, matching the overall display's red accent strategy.

        Args:
            black_draw: PIL ImageDraw context for black channel. Used for weekday,
                month, year, and decorative elements.
            red_draw: Optional PIL ImageDraw context for red channel. When provided,
                the day number is drawn in red; otherwise drawn in black.
            **kwargs: Unused. Current date is obtained from DateTimeUtil.now().

        Layout:
            - Weekday (y=qy+70): Centered, 60pt Geomini
            - Date (y=qy+145): Centered composition of:
              * Day number: 72pt Henny Penny (red/black)
              * Month Year: 44pt Geomini (black), offset +10px down for baseline alignment

        Note:
            This method fetches current date internally rather than using kwargs,
            ensuring date accuracy regardless of when the refresh was triggered.
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
        """Draw black decorative elements around date widget.

        Adds ornamental borders and separators to frame the date information:
        - Scalloped border at top edge (semi-circular arcs)
        - Scalloped border at bottom edge (inverted semi-circular arcs)
        - Diamond separators flanking the date text (left and right)
        - Dotted horizontal rules above and below text area

        Args:
            black_draw: PIL ImageDraw context for black channel.

        Note:
            Scallops start at x=10 (not 0) to avoid edge overflow. Each scallop
            is 26px wide with 30px spacing, creating a repeating arch pattern.
            Called only during full refresh.
        """
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
        """Draw red decorative accent elements.

        Adds red ornamental touches that create warmth and visual interest:
        - Red hearts flanking the weekday (classic calendar motif)
        - Red stars at bottom corners (symmetrical accents)

        Args:
            red_draw: PIL ImageDraw context for red channel.

        Heart Construction:
            Hearts are drawn as two circles (for rounded tops) plus a triangle
            (for the pointed bottom), creating a recognizable heart shape.

        Note:
            Called only during full refresh (every 15 minutes). Red elements require
            full refresh to activate or erase due to e-paper hardware limitations.
        """
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
        """Draw a star polygon shape.

        Creates a star by alternating between outer and inner radii around a center point.
        Used for decorative red accents at bottom corners of the date widget.

        Args:
            draw: PIL ImageDraw context (black or red channel).
            cx: X coordinate of star center.
            cy: Y coordinate of star center.
            outer_r: Radius to outer points (tips of star).
            inner_r: Radius to inner points (valleys between tips).
            points: Number of star points. Defaults to 5 (classic five-pointed star).

        Algorithm:
            Generates 2*points vertices by alternating between outer_r and inner_r
            at evenly spaced angles, starting from top (-π/2) and rotating clockwise.
        """
        import math
        coords = []
        for i in range(points * 2):
            angle = math.pi * (i / points) - math.pi / 2
            r = outer_r if i % 2 == 0 else inner_r
            coords.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        draw.polygon(coords, fill=0)
