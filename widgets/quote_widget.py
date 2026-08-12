"""Quote widget - displays quote of the day with author."""
import logging
import os

from PIL import ImageDraw, ImageFont

from services.quote.zenquotes_service import ZenQuotesService
from widgets.widget import Widget, WidgetRegion

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger(__name__)


class QuoteWidget(Widget):
    """Displays quote in bottom-right area (400x240)."""

    def __init__(self):
        super().__init__(WidgetRegion(x=400, y=240, width=400, height=240))

        self.quote_service = ZenQuotesService()

    def draw(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None = None, **kwargs):
        """Draw quote text and author.

        Args:
            black_draw: PIL ImageDraw for black channel
            red_draw: Optional PIL ImageDraw for red channel
            **kwargs: Must include 'quote' (Quote object)
        """
        quote = self.quote_service.get_quote_of_the_day()

        qx, qy, qw, qh = self.region.x, self.region.y, self.region.width, self.region.height
        padding = 30
        available_height = qh - 100  # Reserve space for decorations and author

        # Determine optimal font size based on quote length
        font_sizes = [32, 28, 24, 20]
        author_font_sizes = [24, 22, 20, 18]

        quote_font = None
        author_font = None
        wrapped = []
        line_height = 40

        for i, size in enumerate(font_sizes):
            try:
                quote_font = ImageFont.truetype(
                    os.path.join(BASE_DIR, "fonts", "PlayfairDisplay-VariableFont_wght.ttf"), size
                )
                author_font = ImageFont.truetype(
                    os.path.join(BASE_DIR, "fonts", "PlayfairDisplay-Italic-VariableFont_wght.ttf"),
                    author_font_sizes[i]
                )
            except OSError:
                # Fallback to Geomini if Playfair not available
                logger.warning(f"Playfair Display not found, using fallback font for size {size}")
                quote_font = ImageFont.truetype(
                    os.path.join(BASE_DIR, "fonts", "Geomini-VariableFont_wght.ttf"), size
                )
                author_font = ImageFont.truetype(
                    os.path.join(BASE_DIR, "fonts", "Geomini-VariableFont_wght.ttf"), author_font_sizes[i]
                )

            # Calculate line height based on font size
            line_height = int(size * 1.3)

            # Try wrapping with this font size
            wrapped = self._wrap_text(quote.text, quote_font, qw - 2 * padding, black_draw)
            total_height = len(wrapped) * line_height

            # If it fits, use this size
            if total_height <= available_height:
                break

        # Opening quote mark (large decorative)
        black_draw.text((qx + padding - 8, qy + 20), "”", font=quote_font, fill=0)

        # Wrap and draw quote text
        y = qy + 60
        for line in wrapped:
            bbox = black_draw.textbbox((0, 0), line, font=quote_font)
            tw = bbox[2] - bbox[0]
            x = qx + (qw - tw) // 2
            black_draw.text((x, y), line, font=quote_font, fill=0)
            y += line_height

        # Closing quote mark
        bbox = black_draw.textbbox((0, 0), "”", font=quote_font)
        qm_w = bbox[2] - bbox[0]
        black_draw.text((qx + qw - padding - qm_w + 8, y - line_height // 2), "”", font=quote_font, fill=0)

        # Author name (centered at bottom)
        author_text = f"— {quote.author}"
        bbox = black_draw.textbbox((0, 0), author_text, font=author_font)
        tw = bbox[2] - bbox[0]
        black_draw.text((qx + (qw - tw) // 2, qy + qh - 50), author_text, font=author_font, fill=0)

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int,
                   draw: ImageDraw.ImageDraw) -> list[str]:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def draw_decorations(self, black_draw: ImageDraw.ImageDraw):
        """Draw black decorative elements."""
        qx, qy, qw, qh = self.region.x, self.region.y, self.region.width, self.region.height

        # Corner brackets for quote section
        for cx, cy, sx, sy in [
            (qx + 15, qy + 15, 1, 1),
            (qx + qw - 15, qy + 15, -1, 1),
            (qx + 15, qy + qh - 15, 1, -1),
            (qx + qw - 15, qy + qh - 15, -1, -1),
        ]:
            black_draw.line([cx, cy, cx + sx * 20, cy], fill=0, width=2)
            black_draw.line([cx, cy, cx, cy + sy * 20], fill=0, width=2)

        # Decorative dots along the top border
        for x in range(qx + 50, qx + qw - 50, 20):
            black_draw.ellipse([x, qy + 8, x + 3, qy + 11], fill=0)

    def draw_red_decorations(self, red_draw: ImageDraw.ImageDraw):
        """Draw red decorative elements."""
        qx, qy = self.region.x, self.region.y

        # Small red diamonds at corners
        for dx, dy in [(qx + 35, qy + 35), (qx + 365, qy + 35)]:
            red_draw.polygon([dx, dy - 4, dx + 4, dy, dx, dy + 4, dx - 4, dy], fill=0)
