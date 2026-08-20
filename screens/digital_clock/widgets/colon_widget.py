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

        # Calculate left-aligned position (colon is narrow, center it manually)
        x = self.region.x + 20  # 20px padding from left
        y = self.region.y + 20  # 20px padding from top

        # Draw colon left-aligned with left-top anchor
        black_draw.text((x, y), ":", font=font, fill=0, anchor='lt')
