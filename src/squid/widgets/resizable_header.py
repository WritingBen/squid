"""Resizable column header widget with draggable separators."""

from __future__ import annotations

from dataclasses import dataclass
from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class ColumnSeparator(Widget):
    """Draggable separator between columns."""

    class Dragged(Message):
        """Separator was dragged."""
        def __init__(self, column_index: int, delta_x: int) -> None:
            super().__init__()
            self.column_index = column_index
            self.delta_x = delta_x

    DEFAULT_CSS = """
    ColumnSeparator {
        width: 1;
        height: 1;
        background: ansi_cyan;
        color: ansi_white;
    }

    ColumnSeparator:hover {
        background: ansi_bright_cyan;
        color: ansi_yellow;
    }

    ColumnSeparator.-dragging {
        background: ansi_white;
        color: ansi_cyan;
    }
    """

    def __init__(self, column_index: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self._column_index = column_index
        self._dragging = False
        self._drag_start_x: int = 0

    def render(self) -> str:
        return "│"

    def on_mouse_down(self, event: events.MouseDown) -> None:
        """Start dragging."""
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
                self.post_message(self.Dragged(self._column_index, delta))
                self._drag_start_x = event.screen_x
            event.stop()

    def on_mouse_up(self, event: events.MouseUp) -> None:
        """Stop dragging."""
        if self._dragging:
            self._dragging = False
            self.release_mouse()
            self.remove_class("-dragging")
            event.stop()


class ColumnHeader(Widget):
    """A single column header label."""

    DEFAULT_CSS = """
    ColumnHeader {
        height: 1;
        background: ansi_cyan;
        color: ansi_black;
        text-style: bold;
    }

    ColumnHeader:hover {
        background: ansi_bright_cyan;
    }
    """

    class Clicked(Message):
        """Column header was clicked (for sorting)."""
        def __init__(self, column_index: int, column_name: str) -> None:
            super().__init__()
            self.column_index = column_index
            self.column_name = column_name

    def __init__(self, name: str, column_index: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self._name = name
        self._column_index = column_index
        self._sort_direction: str | None = None  # None, "asc", "desc"

    def render(self) -> str:
        indicator = ""
        if self._sort_direction == "asc":
            indicator = " ▲"
        elif self._sort_direction == "desc":
            indicator = " ▼"
        return f" {self._name}{indicator}"

    def set_sort_direction(self, direction: str | None) -> None:
        """Set sort indicator: None, 'asc', or 'desc'."""
        self._sort_direction = direction
        self.refresh()

    def on_click(self, event: events.Click) -> None:
        """Handle click for sorting."""
        self.post_message(self.Clicked(self._column_index, self._name))
        event.stop()


@dataclass
class ColumnDef:
    """Column definition."""
    name: str
    width: int
    min_width: int = 5
    resizable: bool = True


class ResizableHeader(Widget):
    """Header row with resizable columns."""

    class ColumnResized(Message):
        """Column was resized."""
        def __init__(self, column_index: int, new_width: int) -> None:
            super().__init__()
            self.column_index = column_index
            self.new_width = new_width

    class ColumnClicked(Message):
        """Column header was clicked (for sorting)."""
        def __init__(self, column_index: int, column_name: str) -> None:
            super().__init__()
            self.column_index = column_index
            self.column_name = column_name

    DEFAULT_CSS = """
    ResizableHeader {
        height: 1;
        width: 100%;
        layout: horizontal;
    }

    ResizableHeader > Horizontal {
        height: 1;
        width: 100%;
    }
    """

    def __init__(self, columns: list[ColumnDef], **kwargs) -> None:
        super().__init__(**kwargs)
        self._columns = columns

    def compose(self) -> ComposeResult:
        with Horizontal():
            for i, col in enumerate(self._columns):
                header = ColumnHeader(col.name, i, id=f"col-header-{i}")
                header.styles.width = col.width
                yield header
                # Add separator after each column except the last
                if i < len(self._columns) - 1 and col.resizable:
                    yield ColumnSeparator(i, id=f"col-sep-{i}")

    def on_column_separator_dragged(self, event: ColumnSeparator.Dragged) -> None:
        """Handle column separator drag."""
        idx = event.column_index
        if 0 <= idx < len(self._columns):
            col = self._columns[idx]
            new_width = max(col.min_width, col.width + event.delta_x)
            col.width = new_width

            # Update the header width
            header = self.query_one(f"#col-header-{idx}", ColumnHeader)
            header.styles.width = new_width

            self.post_message(self.ColumnResized(idx, new_width))

    def on_column_header_clicked(self, event: ColumnHeader.Clicked) -> None:
        """Forward column click for sorting."""
        self.post_message(self.ColumnClicked(event.column_index, event.column_name))

    def get_column_widths(self) -> list[int]:
        """Get current column widths."""
        return [col.width for col in self._columns]

    def set_sort_column(self, column_index: int, direction: str | None) -> None:
        """Set which column is sorted and in which direction."""
        for i, col in enumerate(self._columns):
            header = self.query_one(f"#col-header-{i}", ColumnHeader)
            if i == column_index:
                header.set_sort_direction(direction)
            else:
                header.set_sort_direction(None)
