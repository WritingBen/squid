"""Playlist browser view (View 3)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static, DataTable, Label
from textual.binding import Binding

from squid.widgets.track_list import TrackList

if TYPE_CHECKING:
    from squid.api.models import Playlist, Track


class PlaylistView(Widget):
    """View 3: Playlist browser."""

    BINDINGS = [
        Binding("3", "noop", "Playlists", show=True),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("enter", "select_playlist", "Select", show=False),
        Binding("l", "focus_tracks", "Focus tracks", show=False),
        Binding("h", "focus_playlists", "Focus playlists", show=False),
    ]

    DEFAULT_CSS = """
    PlaylistView {
        layout: horizontal;
        width: 100%;
        height: 100%;
    }

    PlaylistView .playlist-list-pane {
        width: 35%;
        height: 100%;
        border-right: solid ansi_blue;
    }

    PlaylistView .playlist-tracks-pane {
        width: 65%;
        height: 100%;
    }

    PlaylistView .pane-header {
        height: 1;
        background: ansi_blue;
        color: ansi_white;
        padding: 0 1;
    }

    PlaylistView DataTable {
        height: 1fr;
    }
    """

    class PlaylistSelected(Message):
        """Playlist was selected."""

        def __init__(self, playlist: Playlist) -> None:
            super().__init__()
            self.playlist = playlist

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._playlists: list[Playlist] = []
        self._current_playlist: Playlist | None = None
        self._is_mounted = False

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(classes="playlist-list-pane"):
                yield Static("Playlists", classes="pane-header")
                table = DataTable(id="playlist-table", cursor_type="row")
                table.add_columns("Name", "Tracks")
                yield table
            with Vertical(classes="playlist-tracks-pane"):
                yield Static("Tracks", id="tracks-header", classes="pane-header")
                yield TrackList(id="track-list")

    def on_mount(self) -> None:
        """Handle screen mount - populate table if data is available."""
        self._is_mounted = True
        if self._playlists:
            self._populate_table()

    def set_playlists(self, playlists: list[Playlist]) -> None:
        """Set available playlists."""
        self._playlists = playlists
        if self._is_mounted:
            self._populate_table()

    def _populate_table(self) -> None:
        """Populate the playlist table with stored data."""
        table = self.query_one("#playlist-table", DataTable)
        table.clear()
        for playlist in self._playlists:
            table.add_row(
                playlist.title[:35],
                str(playlist.track_count),
                key=playlist.id,
            )

    def set_playlist_tracks(self, playlist: Playlist) -> None:
        """Set tracks for selected playlist."""
        self._current_playlist = playlist
        self.query_one("#tracks-header", Static).update(f"Tracks - {playlist.title}")
        track_list = self.query_one("#track-list", TrackList)
        track_list.set_tracks(playlist.tracks)

    def set_current_track(self, track_id: str | None) -> None:
        """Highlight currently playing track."""
        track_list = self.query_one("#track-list", TrackList)
        track_list.set_current(track_id)

    def action_cursor_down(self) -> None:
        """Move cursor down in playlist table."""
        table = self.query_one("#playlist-table", DataTable)
        if table.has_focus:
            table.action_cursor_down()
        else:
            track_list = self.query_one("#track-list", TrackList)
            track_list.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in playlist table."""
        table = self.query_one("#playlist-table", DataTable)
        if table.has_focus:
            table.action_cursor_up()
        else:
            track_list = self.query_one("#track-list", TrackList)
            track_list.action_cursor_up()

    def action_select_playlist(self) -> None:
        """Select the current playlist (keyboard binding)."""
        table = self.query_one("#playlist-table", DataTable)
        self._select_playlist_row(table.cursor_row)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection from DataTable (click or enter)."""
        # Only handle if it's the playlist table, not the track list
        if event.data_table.id == "playlist-table":
            self._select_playlist_row(event.cursor_row)

    def _select_playlist_row(self, row: int | None) -> None:
        """Select playlist at given row."""
        if row is not None and row < len(self._playlists):
            playlist = self._playlists[row]
            self.post_message(self.PlaylistSelected(playlist))

    def action_focus_tracks(self) -> None:
        """Focus the track list's DataTable."""
        track_list = self.query_one("#track-list", TrackList)
        table = track_list.query_one("#track-table")
        table.focus()

    def action_focus_playlists(self) -> None:
        """Focus the playlist table."""
        self.query_one("#playlist-table", DataTable).focus()

    # PlaylistSelected and TrackList messages bubble naturally to the app

    def action_noop(self) -> None:
        """No-op for view switch key."""
        pass
