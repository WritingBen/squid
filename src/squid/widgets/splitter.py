"""Draggable vertical splitter widget for resizable panes."""

from __future__ import annotations

from textual import events
from textual.message import Message
from textual.widget import Widget


class VerticalSplitter(Widget):
    """A draggable vertical bar that can resize adjacent panes."""

    class Dragged(Message):
        """Splitter was dragged to a new position.

        Attributes:
            delta_x: How many columns the splitter moved (negative = left, positive = right)
        """

        def __init__(self, delta_x: int) -> None:
            super().__init__()
            self.delta_x = delta_x

    DEFAULT_CSS = """
    VerticalSplitter {
        width: 1;
        height: 100%;
        background: ansi_blue;
        color: ansi_white;
    }

    VerticalSplitter:hover {
        background: ansi_bright_blue;
        color: ansi_yellow;
    }

    VerticalSplitter.-dragging {
        background: ansi_cyan;
        color: ansi_white;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._dragging = False
        self._drag_start_x: int = 0
        self._hovered = False

    def render(self) -> str:
        """Render vertical bar with resize indicator."""
        # Use a vertical bar character that suggests draggability
        return "┃"

    def on_enter(self, event: events.Enter) -> None:
        """Handle mouse enter."""
        self._hovered = True
        self.refresh()

    def on_leave(self, event: events.Leave) -> None:
        """Handle mouse leave."""
        self._hovered = False
        self.refresh()

    def on_mouse_down(self, event: events.MouseDown) -> None:
        """Start dragging when mouse is pressed."""
        self._dragging = True
        self._drag_start_x = event.screen_x
        self.capture_mouse()
        self.add_class("-dragging")
        event.stop()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        """Track mouse movement during drag."""
        if self._dragging:
            delta = event.screen_x - self._drag_start_x
            if delta != 0:
                self.post_message(self.Dragged(delta))
                self._drag_start_x = event.screen_x
            event.stop()

    def on_mouse_up(self, event: events.MouseUp) -> None:
        """Stop dragging when mouse is released."""
        if self._dragging:
            self._dragging = False
            self.release_mouse()
            self.remove_class("-dragging")
            event.stop()
