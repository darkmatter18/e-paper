"""AM/PM suffix widget for minimal digital clock.

Displays AM or PM in red.
"""

from PIL import ImageDraw, ImageFont

from settings.fonts import FONT_ORBITRON
from utils.datetime_util import DateTimeUtil
from widgets.base import Widget, WidgetRegion


class AmPmWidget(Widget):
    """AM/PM suffix for minimal digital clock.

    Displays AM or PM in red using Orbitron bold font.
    No partial refresh - only updates on full refresh cycle.

    Colors: Red only
    Updates: Full refresh only (every 15 min / on hour change)
    """

    def __init__(self, region: WidgetRegion):
        """Initialize AM/PM widget.

        Args:
            region: Widget display region
        """
        super().__init__(region)

    @property
    def supports_partial_refresh(self) -> bool:
        """AM/PM widget does not support partial refresh (red channel).

        Returns:
            False, as AM/PM is rendered in red.
        """
        return False

    def draw(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None = None, **kwargs):
        """Draw AM/PM suffix in red.

        Args:
            black_draw: PIL ImageDraw for black channel (unused)
            red_draw: PIL ImageDraw for red channel
            **kwargs: Additional drawing parameters
        """
        if not red_draw:
            return

        # Get current time
        now = DateTimeUtil.now()
        am_pm = now.strftime("%p")  # AM or PM

        # Load Orbitron font - bold (700) for smaller AM/PM text
        font_size = 60
        font = ImageFont.truetype(str(FONT_ORBITRON), font_size)
        font.set_variation_by_axes([700])

        # Calculate dimensions for centering in region
        bbox = red_draw.textbbox((0, 0), am_pm, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Center in region
        x = self.region.x + (self.region.width - text_width) // 2
        y = self.region.y + (self.region.height - text_height) // 2

        # Draw AM/PM
        red_draw.text((x, y), am_pm, font=font, fill=0)
