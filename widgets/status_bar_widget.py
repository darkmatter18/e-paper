"""Status bar widget for system information.

Displays WiFi signal strength and CPU temperature in a macOS-style menu bar.
"""

from PIL import ImageDraw, ImageFont

from fonts import FONT_AWESOME, FONT_GEOMINI
from services.system import SystemService
from widgets.widget import Widget, WidgetRegion


class StatusBarWidget(Widget):
    """Status bar showing WiFi and CPU temperature.

    Displays system information in a horizontal bar at the top of the screen,
    styled like macOS menu bar with WiFi icon, signal dots, and temperature.

    Region: Full width (800x30) at top of display
    Colors: White background, black icons and text
    Updates: Every minute (supports partial refresh)
    """

    # WiFi icon (Font Awesome 7)
    WIFI_ICON = ""  # f1eb - main wifi icon

    def __init__(self, region: WidgetRegion):
        """Initialize status bar widget.

        Args:
            region: Widget display region (typically 0, 0, 800, 30)
        """
        super().__init__(region)
        self.system_service = SystemService()

    @property
    def supports_partial_refresh(self) -> bool:
        """Status bar supports partial refresh for system info updates.

        Returns:
            True, as system info (WiFi, temp) can be rendered in black only.
        """
        return True

    def _get_signal_strength(self, signal_dbm: int) -> int:
        """Get signal strength level (1-4) based on dBm.

        Args:
            signal_dbm: Signal strength in dBm (-100 to 0)

        Returns:
            Signal strength level: 1 (poor) to 4 (excellent)
        """
        if signal_dbm >= -50:
            return 4  # Excellent
        elif signal_dbm >= -60:
            return 3  # Good
        elif signal_dbm >= -70:
            return 2  # Fair
        else:
            return 1  # Poor

    def _draw_signal_dots(self, draw: ImageDraw.ImageDraw, x: int, y: int, strength: int):
        """Draw signal strength as filled/empty circles.

        Args:
            draw: PIL ImageDraw context
            x: Left position
            y: Center Y position
            strength: Signal strength level (1-4)
        """
        dot_radius = 11  # Extra large dots (22px diameter - fills 26px height)
        dot_spacing = 25  # More spacing for larger dots
        total_dots = 4

        for i in range(total_dots):
            # Calculate dot position
            dot_x = x + (i * dot_spacing)
            dot_y = y

            # Draw filled circle if within strength, empty circle otherwise
            if i < strength:
                # Filled circle (black)
                draw.ellipse(
                    [dot_x - dot_radius, dot_y - dot_radius,
                     dot_x + dot_radius, dot_y + dot_radius],
                    fill=0,
                    outline=0
                )
            else:
                # Empty circle (outline only)
                draw.ellipse(
                    [dot_x - dot_radius, dot_y - dot_radius,
                     dot_x + dot_radius, dot_y + dot_radius],
                    fill=255,
                    outline=0,
                    width=1
                )

    def draw(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None = None, **kwargs):
        """Draw status bar with WiFi and CPU temperature.

        Args:
            black_draw: PIL ImageDraw for black channel
            red_draw: PIL ImageDraw for red channel (unused)
            **kwargs: Additional drawing parameters
        """
        # Get system info
        info = self.system_service.get_system_info()

        # Load fonts (extra large sizes to fill ~26px of 30px height)
        icon_font = ImageFont.truetype(str(FONT_AWESOME), 26)
        text_font = ImageFont.truetype(str(FONT_GEOMINI), 22)

        # Prepare status content
        wifi_icon = self.WIFI_ICON
        signal_strength = self._get_signal_strength(info.wifi_strength)
        temp_text = f"{int(info.cpu_temp)}°C"

        # Calculate common vertical center for all elements
        center_y = self.region.y + self.region.height // 2

        # Calculate positions (right-aligned with padding)
        right_padding = 20
        spacing = 14
        current_x = self.region.x + self.region.width - right_padding

        # Draw temperature text (rightmost) - align to center
        temp_bbox = black_draw.textbbox((0, 0), temp_text, font=text_font)
        temp_width = temp_bbox[2] - temp_bbox[0]
        temp_height = temp_bbox[3] - temp_bbox[1]
        temp_x = current_x - temp_width
        temp_y = center_y - temp_height // 2

        black_draw.text((temp_x, temp_y), temp_text, font=text_font, fill=0)

        # Draw signal dots (left of temperature) - use same center
        dots_width = 4 * 22  # 4 dots with 22px spacing
        current_x = temp_x - spacing - dots_width

        self._draw_signal_dots(black_draw, int(current_x), center_y, signal_strength)

        # Draw WiFi icon (left of signal dots) - align to center
        current_x = current_x - spacing
        icon_bbox = black_draw.textbbox((0, 0), wifi_icon, font=icon_font)
        icon_width = icon_bbox[2] - icon_bbox[0]
        icon_height = icon_bbox[3] - icon_bbox[1]
        icon_x = current_x - icon_width
        icon_y = center_y - icon_height // 2

        black_draw.text((icon_x, icon_y), wifi_icon, font=icon_font, fill=0)
