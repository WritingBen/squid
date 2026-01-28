"""Now playing view (View 5)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Center, Middle, Vertical
from textual.widget import Widget
from textual.widgets import Static
from textual.binding import Binding

from squid.widgets.progress_bar import ProgressBar as PlaybackProgressBar

if TYPE_CHECKING:
    from squid.api.models import Track
    from squid.player.state import PlaybackState


class NowPlayingView(Widget):
    """View 5: Large format now playing display."""

    BINDINGS = [
        Binding("4", "noop", "[Playing]", key_display=" ", show=True),
    ]

    DEFAULT_CSS = """
    NowPlayingView {
        layout: vertical;
        width: 100%;
        height: 100%;
        align: center middle;
    }

    NowPlayingView .now-playing-container {
        width: 60%;
        height: auto;
        padding: 2;
        border: round ansi_blue;
        background: $surface;
    }

    NowPlayingView .track-title {
        text-align: center;
        text-style: bold;
        color: $text;
        padding: 1;
    }

    NowPlayingView .track-artist {
        text-align: center;
        color: ansi_cyan;
        padding: 0 1 1 1;
    }

    NowPlayingView .track-album {
        text-align: center;
        color: ansi_bright_black;
        padding: 0 1 2 1;
    }

    NowPlayingView .playback-status {
        text-align: center;
        color: ansi_bright_black;
        padding: 1;
    }

    NowPlayingView .no-track {
        text-align: center;
        color: ansi_bright_black;
        padding: 2;
    }

    NowPlayingView ProgressBar {
        width: 100%;
        margin: 1 0;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_track: Track | None = None

    def compose(self) -> ComposeResult:
        with Center():
            with Middle():
                with Vertical(classes="now-playing-container"):
                    yield Static("No track playing", id="no-track", classes="no-track")
                    yield Static("", id="track-title", classes="track-title")
                    yield Static("", id="track-artist", classes="track-artist")
                    yield Static("", id="track-album", classes="track-album")
                    yield PlaybackProgressBar(id="progress-bar")
                    yield Static("", id="playback-status", classes="playback-status")

    def update_track(self, track: Track | None) -> None:
        """Update displayed track."""
        self._current_track = track

        no_track = self.query_one("#no-track", Static)
        title = self.query_one("#track-title", Static)
        artist = self.query_one("#track-artist", Static)
        album = self.query_one("#track-album", Static)

        if track:
            no_track.display = False
            title.display = True
            artist.display = True
            album.display = True

            title.update(track.title)
            artist.update(track.artist_names)
            album.update(track.album.title if track.album else "")
        else:
            no_track.display = True
            title.display = False
            artist.display = False
            album.display = False

    def update_state(self, state: PlaybackState) -> None:
        """Update playback state display."""
        progress_bar = self.query_one("#progress-bar", PlaybackProgressBar)
        progress_bar.update_from_state(state)

        status = self.query_one("#playback-status", Static)
        status_parts = []

        from squid.player.state import PlayerState, RepeatMode

        if state.state == PlayerState.PLAYING:
            status_parts.append("Playing")
        elif state.state == PlayerState.PAUSED:
            status_parts.append("Paused")
        elif state.state == PlayerState.LOADING:
            status_parts.append("Loading...")
        elif state.state == PlayerState.ERROR:
            status_parts.append(f"Error: {state.error_message}")

        if state.shuffle:
            status_parts.append("[Shuffle]")

        if state.repeat == RepeatMode.ALL:
            status_parts.append("[Repeat All]")
        elif state.repeat == RepeatMode.ONE:
            status_parts.append("[Repeat One]")

        status_parts.append(f"Volume: {state.volume}%")

        status.update("  ".join(status_parts))

        if state.current_track != self._current_track:
            self.update_track(state.current_track)

    def action_noop(self) -> None:
        """No-op for view switch key."""
        pass
