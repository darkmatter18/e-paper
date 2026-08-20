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
        """Draw minutes in black with fixed bounding box for ghosting-free partial refresh.

        Args:
            black_draw: PIL ImageDraw for black channel
            red_draw: PIL ImageDraw for red channel (unused)
            **kwargs: Additional drawing parameters
        """
        # STEP 1: Draw fixed white rectangle with black border for testing
        # This ensures every partial refresh starts with a clean slate
        black_draw.rectangle(
            [
                self.region.x,
                self.region.y,
                self.region.x + self.region.width - 1,
                self.region.y + self.region.height - 1,
            ],
            fill=255,  # White background
            outline=0,  # Black border for testing/debugging
            width=2,
        )

        # STEP 2: Get current time
        now = DateTimeUtil.now()
        minutes = now.strftime("%M")  # Minutes with leading zero

        # STEP 3: Load Orbitron - extra bold weight (900)
        # Fixed bounding box approach works with any font (proportional or monospaced)
        font_size = 180
        font = ImageFont.truetype(str(FONT_ORBITRON), font_size)
        font.set_variation_by_axes([900])  # Extra bold

        # STEP 4: Calculate left-aligned position within the fixed bounding box
        # Left anchor provides most consistent pixel positioning
        x = self.region.x + 20  # 20px padding from left edge
        y = self.region.y + 20  # 20px padding from top edge

        # STEP 5: Draw minutes left-aligned with left-top anchor
        # Left alignment eliminates horizontal shifting completely
        black_draw.text((x, y), minutes, font=font, fill=0, anchor='lt')
