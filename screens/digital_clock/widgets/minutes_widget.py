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
        # STEP 1: Draw fixed white rectangle to clear the region completely
        # This ensures every partial refresh starts with a clean slate
        black_draw.rectangle(
            [
                self.region.x,
                self.region.y,
                self.region.x + self.region.width - 1,
                self.region.y + self.region.height - 1,
            ],
            fill=255,  # White background
            outline=None,
        )

        # STEP 2: Get current time
        now = DateTimeUtil.now()
        minutes = now.strftime("%M")  # Minutes with leading zero

        # STEP 3: Load Orbitron - extra bold weight (900)
        # Fixed bounding box approach works with any font (proportional or monospaced)
        font_size = 180
        font = ImageFont.truetype(str(FONT_ORBITRON), font_size)
        font.set_variation_by_axes([900])  # Extra bold

        # STEP 4: Calculate center position within the fixed bounding box
        center_x = self.region.x + self.region.width // 2
        center_y = self.region.y + self.region.height // 2

        # STEP 5: Draw minutes at center with middle-middle anchor
        # Since we cleared the box first, any minor pixel shifts don't cause ghosting
        black_draw.text((center_x, center_y), minutes, font=font, fill=0, anchor='mm')
