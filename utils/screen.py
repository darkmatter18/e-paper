"""Screen abstraction for managing widget collections.

A Screen represents a collection of widgets that are rendered together to the
e-paper display. It provides a clean interface for widget management and queries,
separating the widget composition from the rendering framework.
"""

from widgets.base import Widget


class Screen:
    """Manages a collection of widgets for display rendering.

    A Screen acts as a container and coordinator for multiple widgets, providing
    methods to query and iterate over them. This abstraction allows for:
    - Multiple screen configurations (e.g., clock screen, settings screen)
    - Clean separation between widget composition and rendering logic
    - Easy widget queries (all widgets, partial-refresh widgets, etc.)

    Attributes:
        widgets (list[Widget]): Ordered list of widgets in this screen.
                               Widgets are rendered in list order.
        name (str): Optional name identifier for this screen.
    """

    def __init__(self, widgets: list[Widget], name: str = "default"):
        """Initialize screen with a list of widgets.

        Args:
            widgets: List of Widget instances to display on this screen.
                    Order determines rendering order.
            name: Optional identifier for this screen (default: "default").
        """
        self.widgets = widgets
        self.name = name

    def get_all_widgets(self) -> list[Widget]:
        """Get all widgets in this screen.

        Returns:
            List of all Widget instances in rendering order.
        """
        return self.widgets

    def get_partial_refresh_widgets(self) -> list[Widget]:
        """Get widgets that support partial refresh.

        Returns:
            List of Widget instances with supports_partial_refresh=True.
            These widgets can be updated without full display refresh.
        """
        return [widget for widget in self.widgets if widget.supports_partial_refresh]

    def has_partial_refresh_widgets(self) -> bool:
        """Check if any widgets support partial refresh.

        Returns:
            True if at least one widget supports partial refresh, False otherwise.
        """
        return any(widget.supports_partial_refresh for widget in self.widgets)

    def get_widget_by_type(self, widget_type: type) -> Widget | None:
        """Get first widget of specified type.

        Args:
            widget_type: Widget class type to search for.

        Returns:
            First widget instance of specified type, or None if not found.
        """
        for widget in self.widgets:
            if isinstance(widget, widget_type):
                return widget
        return None

    def __len__(self) -> int:
        """Get number of widgets in screen.

        Returns:
            Count of widgets in this screen.
        """
        return len(self.widgets)

    def __iter__(self):
        """Iterate over widgets in rendering order.

        Returns:
            Iterator over widget list.
        """
        return iter(self.widgets)

    def __repr__(self) -> str:
        """String representation of screen.

        Returns:
            String showing screen name and widget count.
        """
        widget_names = [w.__class__.__name__ for w in self.widgets]
        return f"Screen(name='{self.name}', widgets=[{', '.join(widget_names)}])"
