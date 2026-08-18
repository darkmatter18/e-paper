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
        """Draw hours in red with fixed positioning.

        Args:
            black_draw: PIL ImageDraw for black channel (unused)
            red_draw: PIL ImageDraw for red channel
            **kwargs: Additional drawing parameters
        """
        if not red_draw:
            return

        # Get current time
        now = DateTimeUtil.now()
        hours = now.strftime("%I")  # 12-hour format with leading zero

        # Load Orbitron font - extra bold (900)
        font_size = 180
        font = ImageFont.truetype(str(FONT_ORBITRON), font_size)
        font.set_variation_by_axes([900])

        # Use fixed position based on widest possible content ("88")
        # to prevent text shifting when hour changes (e.g., 09→10, 11→12).
        # This ensures visual stability - digits stay in same position all day.
        reference_bbox = red_draw.textbbox((0, 0), "88", font=font)
        reference_width = reference_bbox[2] - reference_bbox[0]
        reference_height = reference_bbox[3] - reference_bbox[1]

        # Calculate fixed position (centered based on reference "88")
        x = self.region.x + (self.region.width - reference_width) // 2
        y = self.region.y + (self.region.height - reference_height) // 2

        # Draw hours at fixed position
        red_draw.text((x, y), hours, font=font, fill=0)
