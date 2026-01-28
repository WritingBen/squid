"""Playback progress bar widget."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import ProgressBar as TextualProgressBar, Label
from textual.containers import Horizontal

from squid.player.state import PlaybackState


class ProgressBar(Widget):
    """Playback progress bar with time display."""

    DEFAULT_CSS = """
    ProgressBar {
        height: 1;
        width: 100%;
    }

    ProgressBar Horizontal {
        width: 100%;
    }

    ProgressBar .progress-time-left {
        width: 10;
        color: ansi_bright_black;
    }

    ProgressBar .progress-bar {
        width: 1fr;
    }

    ProgressBar .progress-time-right {
        width: 10;
        text-align: right;
        color: ansi_bright_black;
    }
    """

    progress: reactive[float] = reactive(0.0)
    position_str: reactive[str] = reactive("0:00")
    duration_str: reactive[str] = reactive("0:00")

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("0:00", id="time-left", classes="progress-time-left")
            yield TextualProgressBar(
                total=100, show_eta=False, show_percentage=False, id="bar", classes="progress-bar"
            )
            yield Label("0:00", id="time-right", classes="progress-time-right")

    def watch_progress(self, progress: float) -> None:
        """Update progress bar when progress changes."""
        bar = self.query_one("#bar", TextualProgressBar)
        bar.progress = progress

    def watch_position_str(self, value: str) -> None:
        """Update left time display."""
        self.query_one("#time-left", Label).update(value)

    def watch_duration_str(self, value: str) -> None:
        """Update right time display."""
        self.query_one("#time-right", Label).update(value)

    def update_from_state(self, state: PlaybackState) -> None:
        """Update progress from playback state."""
        self.progress = state.progress_percent
        self.position_str = state.position_str
        self.duration_str = state.duration_str
