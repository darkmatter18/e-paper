"""Quote widget - displays quote of the day with author.

This module implements an inspirational quote display widget showing daily quotes
from ZenQuotes API. Designed for the bottom-right area (400x240) of the 800x480
e-paper display.

Features:
    - Quote text with adaptive font sizing (32pt down to 20pt based on length)
    - Decorative opening and closing quotation marks
    - Author attribution centered at bottom
    - Automatic text wrapping to fit available width
    - Elegant typography using Playfair Display (serif font for literary feel)

Typography:
    - Quote text: Playfair Display Variable (32/28/24/20pt, auto-sized)
    - Author: Playfair Display Italic Variable (24/22/20/18pt, auto-sized)
    - Fallback: Geomini Variable if Playfair not available

Font Sizing Strategy:
    Widget tries progressively smaller font sizes until the wrapped text fits
    within available height (qh - 100px). This ensures long quotes don't overflow
    while short quotes get maximum visual impact.

Color Usage:
    - Black: All text (quote + author), decorative elements
    - No red elements in quote widget (maintains focus on text)

Layout:
    - Opening quote mark: Top-left with padding
    - Quote text: Centered, auto-wrapped, with line_height = size * 1.3
    - Closing quote mark: Bottom-right of last line
    - Author: Bottom center with "—" prefix

Data Source:
    Quotes fetched from ZenQuotes API via ZenQuotesService with daily caching.
"""
import logging

from PIL import ImageDraw, ImageFont

from fonts import FONT_GEOMINI, FONT_PLAYFAIR, FONT_PLAYFAIR_ITALIC
from services.quote.zenquotes_service import ZenQuotesService
from widgets.widget import Widget, WidgetRegion

logger = logging.getLogger(__name__)


class QuoteWidget(Widget):
    """Displays quote in bottom-right area (400x240).

    Shows daily inspirational quote with author attribution. Quotes are fetched
    from ZenQuotes API and cached daily by the internal service.

    Design Philosophy:
        The quote widget provides a moment of reflection and inspiration. Clean
        typography and generous spacing let the words breathe, while decorative
        quotation marks add elegance without overwhelming the message.

    Adaptive Typography:
        Font size automatically scales based on quote length, ensuring both short
        maxims and longer passages fit gracefully within the available space.

    Attributes:
        region: WidgetRegion(x=400, y=240, width=400, height=240) - bottom-right area
        quote_service: ZenQuotesService instance for fetching daily quotes
    """

    def __init__(self, region: WidgetRegion | None = None):
        """Initialize quote widget with ZenQuotes service.

        Args:
            region: Widget display region (defaults to bottom-right quadrant)

        Creates a self-contained widget that handles quote fetching and caching
        internally via ZenQuotesService.
        """
        if region is None:
            region = WidgetRegion(x=400, y=240, width=400, height=240)
        super().__init__(region)
        self.quote_service = ZenQuotesService()

    def draw(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None = None, **kwargs):
        """Draw quote text with author attribution.

        Fetches quote internally and renders with adaptive font sizing, automatic
        text wrapping, decorative quotation marks, and centered author attribution.

        Args:
            black_draw: PIL ImageDraw context for black channel. All quote elements
                are drawn in black for clarity and readability.
            red_draw: Optional PIL ImageDraw context for red channel (unused).
                Quote widget uses black-only to maintain focus on text.
            **kwargs: Unused. Quote is fetched via self.quote_service.

        Font Sizing:
            Tries font sizes in order: [32, 28, 24, 20] pt for quote text
            with corresponding author sizes: [24, 22, 20, 18] pt.
            Uses first size where wrapped text fits in (qh - 100) px.

        Layout:
            - Opening "”": Top-left at (qx + padding - 8, qy + 20)
            - Quote lines: Centered horizontally, starting at y=qy+60
            - Closing "”": Bottom-right of last line at (y - line_height/2)
            - Author: Centered at (qy + qh - 50) with "—" prefix

        Text Wrapping:
            _wrap_text() splits on word boundaries to fit max_width (qw - 2*padding).
            Line height is calculated as size * 1.3 for comfortable reading.

        Fallback:
            If Playfair Display fonts not found, falls back to Geomini Variable
            and logs a warning. This ensures the widget works even with missing fonts.

        Note:
            This method fetches quote internally rather than using kwargs, ensuring
            quote consistency with daily caching handled by the service layer.
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
                quote_font = ImageFont.truetype(str(FONT_PLAYFAIR), size)
                author_font = ImageFont.truetype(str(FONT_PLAYFAIR_ITALIC), author_font_sizes[i])
            except OSError:
                # Fallback to Geomini if Playfair not available
                logger.warning(f"Playfair Display not found, using fallback font for size {size}")
                quote_font = ImageFont.truetype(str(FONT_GEOMINI), size)
                author_font = ImageFont.truetype(str(FONT_GEOMINI), author_font_sizes[i])

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
        """Wrap text to fit within max_width using word boundaries.

        Implements greedy line wrapping algorithm: adds words to current line
        until adding another would exceed max_width, then starts a new line.

        Args:
            text: The quote text to wrap.
            font: PIL FreeTypeFont to use for width measurement.
            max_width: Maximum line width in pixels.
            draw: PIL ImageDraw context for text measurement (textbbox).

        Returns:
            List of wrapped text lines, each fitting within max_width.

        Algorithm:
            1. Split text into words
            2. For each word:
               - Try adding to current line
               - Measure width with textbbox
               - If fits, add word; if not, start new line
            3. Append final line if non-empty

        Note:
            Uses textbbox for accurate width measurement including kerning
            and font-specific spacing. Empty lines are never added to output.
        """
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
        """Draw black decorative elements around quote widget.

        Adds elegant framing elements that complement the literary nature of quotes:
        - Corner brackets at all four corners (L-shaped, 20px arms)
        - Dotted border along top edge (3px dots, 20px spacing)

        Args:
            black_draw: PIL ImageDraw context for black channel.

        Design Rationale:
            Corner brackets create a "framed" effect like a picture or poster,
            appropriate for inspirational quotes. Dotted top border adds subtle
            texture without competing with text. No bottom border decoration to
            keep focus on author attribution.

        Note:
            Called only during full refresh. Decorations are static and complement
            the quote content without overwhelming it.
        """
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
        """Draw red decorative accent elements.

        Adds minimal red diamond accents at top corners to coordinate with the
        overall display's red accent strategy without distracting from quote text.

        Args:
            red_draw: PIL ImageDraw context for red channel.

        Design Rationale:
            Quote widget uses minimal red decoration to maintain focus on text
            content. Small diamonds provide visual connection to other widgets'
            red accents while remaining subtle and unobtrusive.

        Note:
            Called only during full refresh. Red elements require full refresh
            to activate or erase due to e-paper hardware limitations.
        """
        qx, qy = self.region.x, self.region.y

        # Small red diamonds at corners
        for dx, dy in [(qx + 35, qy + 35), (qx + 365, qy + 35)]:
            red_draw.polygon([dx, dy - 4, dx + 4, dy, dx, dy + 4, dx - 4, dy], fill=0)
