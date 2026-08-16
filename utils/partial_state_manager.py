"""Partial refresh state management for e-paper display widgets.

This module provides the PartialStateManager class which tracks previous widget
states for e-paper partial refresh operations. The e-paper controller requires
both old and new buffers to determine which pixels to update during partial refresh.
"""

from PIL import Image

from widgets.widget import Widget


class PartialStateManager:
    """Manages previous state for partial refresh widgets.

    The e-paper controller needs both old and new buffers to determine which
    pixels to update during partial refresh. This manager stores the previous
    region image for each widget that supports partial refresh, enabling proper
    comparison and clean updates without ghosting.

    Attributes:
        _states (dict): Maps widget class names (str) to their previous PIL Image regions.
                       Only widgets with supports_partial_refresh=True are tracked.
                       Keys are widget class names (e.g., "ClockWidget", "DateWidget").
    """

    def __init__(self):
        """Initialize state manager with empty state dictionary."""
        self._states: dict[str, Image.Image] = {}

    def get_old_region(self, widget: Widget) -> Image.Image | None:
        """Get previous region image for a widget.

        Args:
            widget: Widget instance to retrieve state for.

        Returns:
            PIL Image of the widget's previous region, or None if no state exists.
            Returns None on first partial refresh after full refresh.
        """
        widget_key = widget.__class__.__name__
        return self._states.get(widget_key)

    def update_state(self, widget: Widget, new_region: Image.Image) -> None:
        """Update stored state for a widget.

        Stores a copy of the region image to preserve state even if the original
        image is modified. Uses widget class name as key.

        Args:
            widget: Widget instance to update state for.
            new_region: New PIL Image region to store. Image is copied to prevent
                       external modifications from affecting stored state.
        """
        widget_key = widget.__class__.__name__
        self._states[widget_key] = new_region.copy()

    def update_from_full_frame(
        self,
        full_frame: Image.Image,
        all_widgets: list[Widget],
        extract_region_func
    ) -> None:
        """Extract and store regions for all partial-refresh widgets from full frame.

        Called after full refresh to initialize state for subsequent partial refreshes.
        Only extracts regions for widgets with supports_partial_refresh=True.

        Args:
            full_frame: Full display PIL Image (800x480) in mode '1' (black channel).
                       This should be the black channel image after full display.
            all_widgets: List of all widget instances to check for partial refresh support.
            extract_region_func: Function to extract region from image (avoids circular import).
        """
        for widget in all_widgets:
            if widget.supports_partial_refresh:
                region = widget.region
                extracted = extract_region_func(
                    full_frame, region.x, region.y, region.width, region.height
                )
                self.update_state(widget, extracted)

    def has_state(self) -> bool:
        """Check if manager has any stored widget state.

        Returns:
            True if at least one widget state is stored, False if manager is empty.
            Used to determine if partial refresh is possible.
        """
        return len(self._states) > 0
