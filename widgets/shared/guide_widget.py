"""Guide widget for screen layout debugging.

Draws crosshair lines at the center of the screen to help position widgets.
"""

from PIL import ImageDraw

from widgets.base import Widget, WidgetRegion


class GuideWidget(Widget):
    """Debug guide showing center crosshairs.

    Draws black vertical and horizontal lines at screen center (400, 240)
    to help visualize widget positioning during development.

    Region: Full screen (800x480)
    Colors: Black only
    Updates: Static (no refresh needed)
    """

    def __init__(self, region: WidgetRegion):
        """Initialize guide widget.

        Args:
            region: Widget display region (typically full screen: 0, 0, 800, 480)
        """
        super().__init__(region)

    @property
    def supports_partial_refresh(self) -> bool:
        """Guide widget does not support partial refresh (static debug element).

        Returns:
            False, as guide is static and doesn't need updates.
        """
        return False

    def draw(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None = None, **kwargs):
        """Draw center crosshairs.

        Args:
            black_draw: PIL ImageDraw for black channel
            red_draw: PIL ImageDraw for red channel (unused)
            **kwargs: Additional drawing parameters
        """
        # Calculate center of screen
        center_x = self.region.x + self.region.width // 2
        center_y = self.region.y + self.region.height // 2

        # Draw vertical line at center (top to bottom)
        black_draw.line(
            [(center_x, self.region.y), (center_x, self.region.y + self.region.height)],
            fill=0,
            width=1
        )

        # Draw horizontal line at center (left to right)
        black_draw.line(
            [(self.region.x, center_y), (self.region.x + self.region.width, center_y)],
            fill=0,
            width=1
        )
