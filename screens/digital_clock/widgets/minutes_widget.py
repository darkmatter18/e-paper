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
        """Draw minutes in black with fixed positioning for partial refresh.

        Args:
            black_draw: PIL ImageDraw for black channel
            red_draw: PIL ImageDraw for red channel (unused)
            **kwargs: Additional drawing parameters
        """
        # Get current time
        now = DateTimeUtil.now()
        minutes = now.strftime("%M")  # Minutes with leading zero

        # Load Orbitron font - extra bold (900)
        font_size = 180
        font = ImageFont.truetype(str(FONT_ORBITRON), font_size)
        font.set_variation_by_axes([900])

        # CRITICAL: Use fixed position based on widest possible content ("88")
        # to prevent text shifting during partial refresh.
        # Dynamic centering causes ghosting as different digits have slightly different widths.
        reference_bbox = black_draw.textbbox((0, 0), "88", font=font)
        reference_width = reference_bbox[2] - reference_bbox[0]
        reference_height = reference_bbox[3] - reference_bbox[1]

        # Calculate fixed position (centered based on reference "88")
        x = self.region.x + (self.region.width - reference_width) // 2
        y = self.region.y + (self.region.height - reference_height) // 2

        # Draw minutes at fixed position
        black_draw.text((x, y), minutes, font=font, fill=0)
