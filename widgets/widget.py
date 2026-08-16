"""Base widget interface for e-paper display.

This module provides the abstract base class and data structures for all display widgets
in the e-paper clock system. Widgets are modular components that render specific content
(clock, date, weather, quote) within defined rectangular regions of the 800x480 display.

Key Concepts:
    - Dual-channel rendering: Widgets draw to separate black and red image buffers
    - Hardware constraints: Red pigment requires full refresh; partial refresh is black-only
    - Region-based layout: Each widget owns a WidgetRegion defining its drawing area
    - Decorative separation: Content drawing is separated from decorative elements

Typical Usage:
    class MyWidget(Widget):
        def __init__(self):
            super().__init__(WidgetRegion(x=0, y=0, width=400, height=240))

        def draw(self, black_draw, red_draw=None, **kwargs):
            # Draw content
            pass
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from PIL import ImageDraw


@dataclass
class WidgetRegion:
    """Defines the rectangular region where a widget is drawn.

    Widgets use this to know their coordinate space on the 800x480 e-paper display.
    All drawing operations should be relative to the region's origin (x, y).

    Attributes:
        x: Top-left X coordinate in display space (0-800).
        y: Top-left Y coordinate in display space (0-480).
        width: Width of the region in pixels.
        height: Height of the region in pixels.
    """
    x: int
    y: int
    width: int
    height: int


class Widget(ABC):
    """Abstract base class for all display widgets.

    Widgets are self-contained components that render content within a defined region
    of the e-paper display. They handle both full refresh (with red channel) and
    partial refresh (black-only) rendering strategies.

    Hardware Considerations:
        - Waveshare 7.5" B/V2 display has 3 colors: Black, White, Red
        - Red pigment activation requires full (flashing) refresh
        - Partial refresh can only update black pixels (red remains unchanged)
        - Widgets that need red accents should render them only when red_draw is provided

    Attributes:
        region: The WidgetRegion defining this widget's drawing area.

    Subclass Responsibilities:
        - Implement draw() to render widget content
        - Optionally override draw_decorations() for black decorative elements
        - Optionally override draw_red_decorations() for red decorative elements
        - Set supports_partial_refresh property if widget can use partial refresh
    """

    def __init__(self, region: WidgetRegion):
        """Initialize widget with its display region.

        Args:
            region: The rectangular area where this widget draws. The widget
                should constrain all drawing operations within this region.
        """
        self.region = region

    @abstractmethod
    def draw(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None = None, **kwargs):
        """Draw the widget content.

        This is the main rendering method called during both full and partial refresh.
        Implementations should check if red_draw is None to determine the refresh type.

        Args:
            black_draw: PIL ImageDraw context for the black channel. All widgets must
                draw their primary content to this channel.
            red_draw: PIL ImageDraw context for the red channel, or None during partial
                refresh. Red accent elements should only be drawn when this is provided.
            **kwargs: Additional data needed by the widget. Common keys include:
                - 'now': datetime object for current time
                - 'quote': Quote object for quote widgets
                - 'weather': WeatherData object for weather widgets

        Note:
            During partial refresh, red_draw will be None. Widgets should draw any
            elements that would normally be red in black instead, or skip them entirely
            if they don't change between full refreshes.
        """

    def draw_decorations(self, black_draw: ImageDraw.ImageDraw):
        """Draw black decorative elements around the widget.

        Called during full refresh to add ornamental elements (borders, dots, brackets,
        flourishes) around the widget's main content. These are purely aesthetic and
        should not contain functional information.

        Args:
            black_draw: PIL ImageDraw context for the black channel.

        Note:
            Default implementation does nothing. Override to add decorations.
        """

    def draw_red_decorations(self, red_draw: ImageDraw.ImageDraw):
        """Draw red decorative elements around the widget.

        Called only during full refresh to add red accent elements. These are purely
        aesthetic and should not contain functional information that users rely on.

        Args:
            red_draw: PIL ImageDraw context for the red channel.

        Note:
            Default implementation does nothing. Override to add red decorations.
            This method is NEVER called during partial refresh.
        """

    @property
    def supports_partial_refresh(self) -> bool:
        """Whether this widget can be updated via partial refresh (black-only).

        Widgets that support partial refresh can be updated between full refreshes
        to show dynamic content (e.g., clock minute hand) without flashing the display.

        Hardware Constraint:
            Partial refresh on Waveshare 7.5" B/V2 can only update black pixels.
            Any red elements will remain unchanged from the last full refresh.

        Returns:
            True if widget can be meaningfully updated via partial refresh,
            False if it requires full refresh (e.g., contains red elements that change).

        Note:
            Default is False. Override and return True only if the widget's content
            changes frequently and can be rendered entirely in black during updates.
        """
        return False
