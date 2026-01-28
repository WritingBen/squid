"""Status bar widget showing playback state."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label

from squid.player.state import PlaybackState, PlayerState, RepeatMode


class StatusBar(Widget):
    """Bottom status bar showing playback state and current track."""

    DEFAULT_CSS = """
    StatusBar {
        width: 100%;
        height: 1;
        background: $surface;
    }

    StatusBar Horizontal {
        width: 100%;
    }

    StatusBar .status-state {
        width: 5;
        color: ansi_green;
    }

    StatusBar .status-track {
        width: 1fr;
        color: $text;
    }

    StatusBar .status-modes {
        width: 6;
        text-align: right;
        color: ansi_magenta;
    }
    """

    playback_state: reactive[PlaybackState] = reactive(PlaybackState)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("", id="state", classes="status-state")
            yield Label("", id="track", classes="status-track")
            yield Label("", id="modes", classes="status-modes")

    def watch_playback_state(self, state: PlaybackState) -> None:
        """Update display when playback state changes."""
        self._update_display(state)

    def _update_display(self, state: PlaybackState) -> None:
        """Update all status bar elements."""
        # State indicator
        state_label = self.query_one("#state", Label)
        state_icons = {
            PlayerState.STOPPED: "[ ]",
            PlayerState.PLAYING: "[>]",
            PlayerState.PAUSED: "[||]",
            PlayerState.LOADING: "[..]",
            PlayerState.ERROR: "[!]",
        }
        state_label.update(state_icons.get(state.state, "[ ]"))

        # Track info
        track_label = self.query_one("#track", Label)
        if state.current_track:
            track_label.update(
                f"{state.current_track.artist_names} - {state.current_track.title}"
            )
        else:
            track_label.update("")

        # Modes (shuffle/repeat)
        modes_label = self.query_one("#modes", Label)
        modes = ""
        if state.shuffle:
            modes += "S"
        repeat_icons = {
            RepeatMode.OFF: "",
            RepeatMode.ALL: "R",
            RepeatMode.ONE: "R1",
        }
        modes += repeat_icons.get(state.repeat, "")
        modes_label.update(modes)

    def update_state(self, state: PlaybackState) -> None:
        """Public method to update playback state."""
        self.playback_state = state
        # Call _update_display directly since the same state object is reused
        # and Textual's reactive system won't detect changes to the same object
        self._update_display(state)
