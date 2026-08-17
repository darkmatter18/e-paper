"""Status bar widget for system information.

Displays WiFi signal strength and CPU temperature in a macOS-style menu bar.
"""

from typing import ClassVar

from PIL import ImageDraw, ImageFont

from fonts import FONT_AWESOME, FONT_GEOMINI
from services.system import SystemService
from widgets.widget import Widget, WidgetRegion


class StatusBarWidget(Widget):
    """Status bar showing WiFi and CPU temperature.

    Displays system information in a horizontal bar at the top of the screen,
    styled like macOS menu bar with icons on the right side.

    Region: Full width (800x40) at top of display
    Colors: Black background, white icons and text
    Updates: Every minute (supports partial refresh)
    """

    # Font Awesome 7 WiFi icons
    WIFI_ICONS: ClassVar = {
        "excellent": "",  # Full bars (>= -50 dBm)
        "good": "",  # 3 bars (-50 to -60 dBm)
        "fair": "",  # 2 bars (-60 to -70 dBm)
        "poor": "",  # 1 bar (< -70 dBm)
    }

    def __init__(self, region: WidgetRegion):
        """Initialize status bar widget.

        Args:
            region: Widget display region (typically 0, 0, 800, 40)
        """
        super().__init__(region)
        self.system_service = SystemService()

    @property
    def supports_partial_refresh(self) -> bool:
        """Clock supports partial refresh for minute hand updates.

        Returns:
            True, because minute hand position changes frequently and can be
            rendered entirely in black. Hour hand moves slowly enough that
            switching from red to black during partial refresh is acceptable.
        """
        return True

    def _get_wifi_icon(self, signal_dbm: int) -> str:
        """Get WiFi icon based on signal strength.

        Args:
            signal_dbm: Signal strength in dBm (-100 to 0)

        Returns:
            Font Awesome WiFi icon character
        """
        if signal_dbm >= -50:
            return self.WIFI_ICONS["excellent"]
        elif signal_dbm >= -60:
            return self.WIFI_ICONS["good"]
        elif signal_dbm >= -70:
            return self.WIFI_ICONS["fair"]
        else:
            return self.WIFI_ICONS["poor"]

    def draw(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None = None, **kwargs):
        """Draw status bar with WiFi and CPU temperature.

        Args:
            black_draw: PIL ImageDraw for black channel
            red_draw: PIL ImageDraw for red channel (unused)
            **kwargs: Additional drawing parameters
        """
        # Get system info
        info = self.system_service.get_system_info()

        # Load fonts
        icon_font = ImageFont.truetype(str(FONT_AWESOME), 20)
        text_font = ImageFont.truetype(str(FONT_GEOMINI), 16)

        # Draw black background bar
        black_draw.rectangle(
            [
                self.region.x,
                self.region.y,
                self.region.x + self.region.width,
                self.region.y + self.region.height,
            ],
            fill=0,  # Black
        )

        # Prepare status text
        wifi_icon = self._get_wifi_icon(info.wifi_strength)
        temp_text = f"{int(info.cpu_temp)}°C"

        # Calculate positions (right-aligned with padding)
        right_padding = 20
        spacing = 15
        current_x = self.region.x + self.region.width - right_padding

        # Draw temperature text (rightmost)
        temp_bbox = black_draw.textbbox((0, 0), temp_text, font=text_font)
        temp_width = temp_bbox[2] - temp_bbox[0]
        temp_x = current_x - temp_width
        temp_y = self.region.y + (self.region.height - temp_bbox[3]) // 2

        black_draw.text((temp_x, temp_y), temp_text, font=text_font, fill=255)  # White

        # Draw WiFi icon (left of temperature)
        current_x = temp_x - spacing
        icon_bbox = black_draw.textbbox((0, 0), wifi_icon, font=icon_font)
        icon_width = icon_bbox[2] - icon_bbox[0]
        icon_x = current_x - icon_width
        icon_y = self.region.y + (self.region.height - icon_bbox[3]) // 2

        black_draw.text((icon_x, icon_y), wifi_icon, font=icon_font, fill=255)  # White
