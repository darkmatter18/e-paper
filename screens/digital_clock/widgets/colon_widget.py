"""Colon separator widget for minimal digital clock.

Displays static colon separator in black.
"""

from PIL import ImageDraw, ImageFont

from settings.fonts import FONT_ORBITRON
from widgets.base import Widget, WidgetRegion


class ColonWidget(Widget):
    """Colon separator for minimal digital clock.

    Displays ":" in black using Orbitron extra bold font.
    Static element - no updates needed.

    Colors: Black only
    Updates: Full refresh only (static element)
    """

    def __init__(self, region: WidgetRegion):
        """Initialize colon widget.

        Args:
            region: Widget display region
        """
        super().__init__(region)

    @property
    def supports_partial_refresh(self) -> bool:
        """Colon widget does not support partial refresh (static element).

        Returns:
            False, as colon is static and doesn't need updates.
        """
        return False

    def draw(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None = None, **kwargs):
        """Draw colon separator in black.

        Args:
            black_draw: PIL ImageDraw for black channel
            red_draw: PIL ImageDraw for red channel (unused)
            **kwargs: Additional drawing parameters
        """
        # Load Orbitron font - extra bold (900)
        font_size = 180
        font = ImageFont.truetype(str(FONT_ORBITRON), font_size)
        font.set_variation_by_axes([900])

        # Calculate dimensions for centering in region
        bbox = black_draw.textbbox((0, 0), ":", font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Center in region
        x = self.region.x + (self.region.width - text_width) // 2
        y = self.region.y + (self.region.height - text_height) // 2

        # Draw colon
        black_draw.text((x, y), ":", font=font, fill=0)
