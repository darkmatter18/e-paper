"""Clock widget - displays analog clock with digital time.

This module implements a dual-display clock widget combining an analog clock face
with a stacked digital time display (HH/MM/AM-PM). Designed for the upper-left
quadrant (400x240) of the 800x480 e-paper display.

Features:
    - Analog clock with 12 tick marks and smooth hour hand movement
    - Digital time stacked vertically with hour shown in red
    - Supports partial refresh for minute hand updates (black-only)
    - Decorative elements: dot ring, corner brackets, sun/moon indicator
    - Red accents: hour hand, quarter-hour dots, corner stars

Hardware Optimization:
    The clock supports partial refresh because the minute hand can be redrawn in
    black without needing the red channel. The hour hand is drawn in red during
    full refresh, but switches to black during partial refresh (it moves slowly
    enough that color changes are imperceptible between full refreshes).

Coordinate System:
    All drawing is done in absolute display coordinates. The analog clock center
    is at (CX=100, CY=120), and the digital display starts at DIGI_X=240.
"""
import math
from datetime import datetime

from PIL import ImageDraw, ImageFont

from fonts import FONT_GEOMINI
from utils import DateTimeUtil
from widgets.widget import Widget, WidgetRegion

# Clock geometry constants
CX, CY = 100, 120  # Center point of analog clock face in display coordinates
RADIUS = 90  # Outer circle radius in pixels
HOUR_LEN = 50  # Hour hand length from center in pixels
MIN_LEN = 78  # Minute hand length from center in pixels
HUB_R = 5  # Center hub radius in pixels

# Digital clock positioning
DIGI_X = 240  # Left edge X-coordinate of digital time text area

# Fonts for digital time display
FONT_DIGI = ImageFont.truetype(str(FONT_GEOMINI), 52)  # Hours and minutes
FONT_DIGI_SM = ImageFont.truetype(str(FONT_GEOMINI), 36)  # AM/PM indicator


class ClockWidget(Widget):
    """Displays analog clock with digital time in upper-left quadrant (400x240).

    Combines a traditional analog clock face with a modern stacked digital display.
    The analog clock shows smooth hour hand movement (advances with minutes), while
    the digital display shows HH/MM/AM-PM in a vertical stack.

    Layout:
        - Left side: Analog clock centered at (100, 120)
        - Right side: Digital time starting at x=240

    Refresh Strategy:
        - Full refresh: Hour hand drawn in red, all decorations visible
        - Partial refresh: Hour hand drawn in black (changes slowly), minute hand updated

    Color Usage:
        - Black: Clock face, tick marks, minute hand, MM/AM-PM text
        - Red: Hour hand (full refresh only), HH text, decorative accents

    Attributes:
        region: WidgetRegion(x=0, y=0, width=400, height=240) - upper-left quadrant
    """

    def __init__(self):
        """Initialize clock widget with upper-left quadrant region."""
        super().__init__(WidgetRegion(x=0, y=0, width=400, height=240))

    @property
    def supports_partial_refresh(self) -> bool:
        """Clock supports partial refresh for minute hand updates.

        Returns:
            True, because minute hand position changes frequently and can be
            rendered entirely in black. Hour hand moves slowly enough that
            switching from red to black during partial refresh is acceptable.
        """
        return True

    def draw(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None = None, **kwargs):
        """Draw clock face, hands, and digital time display.

        Renders the complete clock widget including static clock face, moving hands,
        and digital time. Hour hand color adapts based on refresh type: red during
        full refresh, black during partial refresh.

        Args:
            black_draw: PIL ImageDraw context for black channel. Used for clock face,
                minute hand, and most digital time elements.
            red_draw: PIL ImageDraw context for red channel, or None during partial
                refresh. When provided, hour hand and hour digits are drawn in red.
            **kwargs: Unused. Current time is obtained from DateTimeUtil.now().

        Note:
            This method fetches current time internally rather than using kwargs,
            ensuring real-time accuracy regardless of when the refresh was triggered.
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
        """Draw static analog clock face elements.

        Renders the circular clock outline, 12 tick marks (with longer marks at
        quarters: 12, 3, 6, 9), and center hub. This is the static background
        behind the moving clock hands.

        Args:
            draw: PIL ImageDraw context for black channel.

        Note:
            Tick marks use math.sin/cos with angle calculation: 2π * (position/12)
            where 0° is top (12 o'clock) and rotation is clockwise.
        """
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
        """Draw hour hand with smooth minute-based advancement.

        Renders the hour hand as a thick line from center to calculated position.
        Unlike traditional clocks that jump between hours, this implementation
        advances smoothly: at 3:30, the hand is halfway between 3 and 4.

        Args:
            draw: PIL ImageDraw context (black or red channel).
            hour: Current hour (0-23). Converted to 12-hour internally.
            minute: Current minute (0-59). Used to calculate fractional hour position.
            fill: Fill color (0 for black/red, 255 for white). Typically 0.

        Algorithm:
            Position = (hour % 12 + minute/60) / 12 * 2π
            This creates smooth 12-hour rotation with minute-precision.
        """
        value = (hour % 12) + minute / 60.0
        angle = 2 * math.pi * (value / 12)
        x = CX + HOUR_LEN * math.sin(angle)
        y = CY - HOUR_LEN * math.cos(angle)
        draw.line([CX, CY, x, y], fill=fill, width=8)

    def _draw_minute_hand(self, draw: ImageDraw.ImageDraw, minute: int, fill: int):
        """Draw minute hand pointing to current minute.

        Renders the minute hand as a medium-weight line from center to calculated
        position. This is the primary moving element during partial refresh.

        Args:
            draw: PIL ImageDraw context (typically black channel).
            minute: Current minute (0-59). Directly maps to 60 positions around the clock.
            fill: Fill color (0 for black, 255 for white). Typically 0.

        Note:
            Updates every minute during partial refresh. Hand length (MIN_LEN=78)
            is longer than hour hand (HOUR_LEN=50) for traditional clock proportions.
        """
        angle = 2 * math.pi * (minute / 60)
        x = CX + MIN_LEN * math.sin(angle)
        y = CY - MIN_LEN * math.cos(angle)
        draw.line([CX, CY, x, y], fill=fill, width=5)

    def _draw_digital(self, draw: ImageDraw.ImageDraw, now: datetime, red_draw: ImageDraw.ImageDraw | None = None):
        """Draw digital time display in stacked HH/MM/AM-PM format.

        Renders three lines of text vertically centered in the right portion of
        the clock widget. Hour is emphasized in red (when available), creating
        visual hierarchy and color coordination with the red hour hand.

        Args:
            draw: PIL ImageDraw context for black channel.
            now: Current datetime object. Used to extract hour, minute, and AM/PM.
            red_draw: Optional PIL ImageDraw context for red channel. When provided,
                the hour line is drawn in red; otherwise drawn in black.

        Layout:
            Line 1 (top): HH in 12-hour format (01-12) - red or black
            Line 2 (middle): MM zero-padded (00-59) - always black
            Line 3 (bottom): AM/PM indicator - always black, smaller font

        Note:
            All three lines are center-aligned within a 120px wide area starting
            at DIGI_X=240. Vertical spacing is 65px between baselines.
        """
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
        """Draw black decorative elements around clock widget.

        Adds ornamental features that enhance the vintage/decorative aesthetic:
        - Dot ring around analog clock (60 dots at minute positions, larger at 5-min marks)
        - Small separator dots between digital time lines
        - Corner flourishes (L-shaped brackets at all 4 corners)
        - Ornamental brackets flanking digital time
        - Sun/moon indicator at top center (sun: 6am-6pm, moon: 6pm-6am)

        Args:
            black_draw: PIL ImageDraw context for black channel.

        Note:
            Called only during full refresh. These decorations are static and don't
            change with time (except sun/moon which updates hourly).
        """
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
        """Draw red decorative accent elements.

        Adds red ornamental touches that complement the red hour hand and hour digits:
        - Red diamond below analog clock
        - Red dots at quarter-hour positions (12, 3, 6, 9) on outer dot ring
        - Small red stars at top corners

        Args:
            red_draw: PIL ImageDraw context for red channel.

        Note:
            Called only during full refresh (every 15 minutes). Red elements require
            full refresh to activate or erase due to e-paper hardware limitations.
        """
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
        """Draw a star polygon shape.

        Creates a star by alternating between outer and inner radii around a center point.
        Used for decorative accents in corners and other ornamental locations.

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
        coords = []
        for i in range(points * 2):
            angle = math.pi * (i / points) - math.pi / 2
            r = outer_r if i % 2 == 0 else inner_r
            coords.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        draw.polygon(coords, fill=0)
