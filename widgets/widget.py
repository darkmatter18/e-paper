"""Base widget interface for e-paper display."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from PIL import ImageDraw


@dataclass
class WidgetRegion:
    """Defines the rectangular region where a widget is drawn."""
    x: int  # Top-left X coordinate
    y: int  # Top-left Y coordinate
    width: int  # Width of the region
    height: int  # Height of the region


class Widget(ABC):
    """Abstract base class for all display widgets."""

    def __init__(self, region: WidgetRegion):
        """Initialize widget with its display region.

        Args:
            region: The rectangular area where this widget draws
        """
        self.region = region

    @abstractmethod
    def draw(self, black_draw: ImageDraw.ImageDraw, red_draw: ImageDraw.ImageDraw | None = None, **kwargs):
        """Draw the widget content.

        Args:
            black_draw: PIL ImageDraw for black channel
            red_draw: Optional PIL ImageDraw for red channel (None during partial refresh)
            **kwargs: Additional data needed by the widget (time, weather, quote, etc.)
        """

    def draw_decorations(self, black_draw: ImageDraw.ImageDraw):
        """Draw black decorative elements around the widget.

        Args:
            black_draw: PIL ImageDraw for black channel
        """

    def draw_red_decorations(self, red_draw: ImageDraw.ImageDraw):
        """Draw red decorative elements around the widget.

        Args:
            red_draw: PIL ImageDraw for red channel
        """

    @property
    def supports_partial_refresh(self) -> bool:
        """Whether this widget can be updated via partial refresh (black-only).

        Returns:
            True if widget can use partial refresh, False if it requires full refresh
        """
        return False
