"""Hours widget for minimal digital clock.

Displays hours in 12-hour format with red color.
"""

from PIL import ImageDraw, ImageFont

from settings.fonts import FONT_ORBITRON
from utils.datetime_util import DateTimeUtil
from widgets.base import Widget, WidgetRegion


class HoursWidget(Widget):
    """Hours display for minimal digital clock.

    Displays hours in red using Orbitron extra bold font.
    No partial refresh - only updates on full refresh cycle.

    Colors: Red only
    Updates: Full refresh only (every 15 min / on hour change)
    """

    def __init__(self, region: WidgetRegion):
        """Initialize hours widget.

        Args:
            region: Widget display region
        """
        super().__init__(region)

    @property
    def supports_partial_refresh(self) -> bool:
        """Hours widget does not support partial refresh (red channel).

        Returns:
            False, as hours are rendered in red.
        """
        return False

    def draw(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None = None, **kwargs):
        """Draw hours in red with fixed bounding box for consistent display.

        Args:
            black_draw: PIL ImageDraw for black channel (unused)
            red_draw: PIL ImageDraw for red channel
            **kwargs: Additional drawing parameters
        """
        if not red_draw:
            return

        # STEP 1: Draw fixed white rectangle to clear the region completely
        # This ensures every refresh starts with a clean slate
        red_draw.rectangle(
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
        hours = now.strftime("%I")  # 12-hour format with leading zero

        # STEP 3: Load Orbitron font - extra bold (900)
        font_size = 180
        font = ImageFont.truetype(str(FONT_ORBITRON), font_size)
        font.set_variation_by_axes([900])

        # STEP 4: Calculate center position within the fixed bounding box
        center_x = self.region.x + self.region.width // 2
        center_y = self.region.y + self.region.height // 2

        # STEP 5: Draw hours at center with middle-middle anchor
        # Since we cleared the box first, any minor pixel shifts don't cause ghosting
        red_draw.text((center_x, center_y), hours, font=font, fill=0, anchor='mm')
