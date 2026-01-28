"""Vertical volume slider widget like Alsamixer."""

from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class VolumeSlider(Widget):
    """Vertical volume slider with Alsamixer-style appearance."""

    class VolumeChanged(Message):
        """Volume was changed by user interaction."""
        def __init__(self, volume: int) -> None:
            super().__init__()
            self.volume = volume

    DEFAULT_CSS = """
    VolumeSlider {
        width: 100%;
        height: 100%;
        background: $surface;
        border: round ansi_blue;
        padding: 0 1;
    }

    VolumeSlider .volume-label {
        height: 1;
        width: 100%;
        text-align: center;
        color: ansi_cyan;
    }

    VolumeSlider .volume-bar-container {
        height: 1fr;
        width: 100%;
    }

    VolumeSlider .volume-percent {
        height: 1;
        width: 100%;
        text-align: center;
        color: ansi_white;
    }
    """

    volume: reactive[int] = reactive(80)

    def compose(self) -> ComposeResult:
        yield Static("Vol", classes="volume-label")
        yield Static("", id="bar-container", classes="volume-bar-container")
        yield Static("80%", id="percent", classes="volume-percent")

    def on_mount(self) -> None:
        """Initialize display."""
        self._update_display()

    def on_resize(self, event: events.Resize) -> None:
        """Update display on resize."""
        self._update_display()

    def watch_volume(self, volume: int) -> None:
        """Update display when volume changes."""
        self._update_display()

    def _update_display(self) -> None:
        """Update the visual representation of volume."""
        # Update percentage label
        self.query_one("#percent", Static).update(f"{self.volume}%")

        # Calculate bar height
        container = self.query_one("#bar-container", Static)
        # Get available height (container height minus borders/padding)
        available_height = max(1, container.size.height)

        # Calculate filled portion
        filled_height = int((self.volume / 100) * available_height)
        empty_height = available_height - filled_height

        # Build vertical bar representation
        # Using block characters: filled = ██, empty = ░░
        lines = []
        for i in range(empty_height):
            lines.append("░░")
        for i in range(filled_height):
            lines.append("██")

        container.update("\n".join(lines))

    def on_click(self, event: events.Click) -> None:
        """Handle click to set volume."""
        container = self.query_one("#bar-container", Static)

        # Get click position relative to container
        # Note: event.y is relative to the widget
        container_y = 1  # After "Vol" label
        available_height = max(1, container.size.height)

        # Calculate relative y within the bar
        click_y = event.y - container_y

        if 0 <= click_y < available_height:
            # Invert because top = high volume
            new_volume = int(((available_height - click_y) / available_height) * 100)
            new_volume = max(0, min(100, new_volume))
            self.volume = new_volume
            self.post_message(self.VolumeChanged(new_volume))

    def set_volume(self, volume: int) -> None:
        """Set volume from external source."""
        self.volume = max(0, min(100, volume))
