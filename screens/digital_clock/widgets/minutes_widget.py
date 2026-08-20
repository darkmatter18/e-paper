"""Minutes widget for minimal digital clock.

Displays minutes in black with partial refresh support.
"""

from PIL import ImageDraw, ImageFont

from settings.fonts import FONT_ORBITRON
from utils.datetime_util import DateTimeUtil
from widgets.base import Widget, WidgetRegion


class MinutesWidget(Widget):
    """Minutes display for minimal digital clock.

    Displays minutes in black using Orbitron extra bold font.
    Supports partial refresh for per-minute updates.

    Colors: Black only
    Updates: Partial refresh every minute
    """

    def __init__(self, region: WidgetRegion):
        """Initialize minutes widget.

        Args:
            region: Widget display region
        """
        super().__init__(region)

    @property
    def supports_partial_refresh(self) -> bool:
        """Minutes widget supports partial refresh.

        Returns:
            True, as minutes are rendered in black and update every minute.
        """
        return True

    def draw(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None = None, **kwargs):
        """Draw minutes in black with left-alignment for ghosting-free partial refresh.

        Args:
            black_draw: PIL ImageDraw for black channel
            red_draw: PIL ImageDraw for red channel (unused)
            **kwargs: Additional drawing parameters
        """
        # Get current time
        now = DateTimeUtil.now()
        minutes = now.strftime("%M")  # Minutes with leading zero

        # Load Orbitron - extra bold weight (900)
        font_size = 180
        font = ImageFont.truetype(str(FONT_ORBITRON), font_size)
        font.set_variation_by_axes([900])  # Extra bold

        # Calculate left-aligned position
        # Left anchor provides consistent pixel positioning for partial refresh
        x = self.region.x + 20  # 20px padding from left edge
        y = self.region.y + 20  # 20px padding from top edge

        # Draw minutes left-aligned with left-top anchor
        # Left alignment eliminates horizontal shifting completely
        black_draw.text((x, y), minutes, font=font, fill=0, anchor='lt')
