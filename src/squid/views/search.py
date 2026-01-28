"""Search view (View 6)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static, Input, DataTable, RadioSet, RadioButton
from textual.binding import Binding

from squid.widgets.track_list import TrackList

if TYPE_CHECKING:
    from squid.api.models import SearchResults, Track, Album, Artist, Playlist


class SearchView(Widget):
    """View 6: Search YouTube Music."""

    BINDINGS = [
        Binding("5", "noop", "[Search]", key_display=" ", show=True),
        Binding("/", "focus_search", "Search", show=False),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("enter", "select", "Select", show=False),
        Binding("a", "add_to_queue", "Add to queue", show=False),
    ]

    DEFAULT_CSS = """
    SearchView {
        layout: vertical;
        width: 100%;
        height: 100%;
    }

    SearchView .search-header {
        height: 3;
        padding: 1;
        background: $surface;
    }

    SearchView .search-header Input {
        width: 100%;
    }

    SearchView .filter-bar {
        height: 3;
        padding: 0 1;
        background: $surface;
    }

    SearchView .pane-header {
        height: 1;
        background: ansi_blue;
        color: ansi_white;
        padding: 0 1;
    }

    SearchView .results-container {
        height: 1fr;
    }

    SearchView RadioSet {
        layout: horizontal;
        height: auto;
    }
    """

    class SearchRequested(Message):
        """Search was requested."""

        def __init__(self, query: str, filter_type: str | None) -> None:
            super().__init__()
            self.query = query
            self.filter_type = filter_type

    class TrackSelected(Message):
        """Track was selected."""

        def __init__(self, track: Track) -> None:
            super().__init__()
            self.track = track

    class AlbumSelected(Message):
        """Album was selected."""

        def __init__(self, album: Album) -> None:
            super().__init__()
            self.album = album

    class ArtistSelected(Message):
        """Artist was selected."""

        def __init__(self, artist: Artist) -> None:
            super().__init__()
            self.artist = artist

    class PlaylistSelected(Message):
        """Playlist was selected."""

        def __init__(self, playlist: Playlist) -> None:
            super().__init__()
            self.playlist = playlist

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._results: SearchResults | None = None
        self._filter_type: str | None = None
        self._current_items: list = []

    def compose(self) -> ComposeResult:
        with Vertical(classes="search-header"):
            yield Input(placeholder="Search YouTube Music...", id="search-input")
        with Horizontal(classes="filter-bar"):
            with RadioSet(id="filter-set"):
                yield RadioButton("All", id="filter-all", value=True)
                yield RadioButton("Songs", id="filter-songs")
                yield RadioButton("Albums", id="filter-albums")
                yield RadioButton("Artists", id="filter-artists")
                yield RadioButton("Playlists", id="filter-playlists")
        yield Static("Results", id="results-header", classes="pane-header")
        with Vertical(classes="results-container"):
            yield TrackList(id="track-list")
            table = DataTable(id="results-table", cursor_type="row")
            table.add_columns("Type", "Name", "Info")
            yield table

    def on_mount(self) -> None:
        """Set up initial state."""
        self.query_one("#results-table", DataTable).display = False

    def action_focus_search(self) -> None:
        """Focus the search input."""
        self.query_one("#search-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search submission."""
        query = event.value.strip()
        if query:
            self.post_message(self.SearchRequested(query, self._filter_type))

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle filter change."""
        filter_map = {
            "filter-all": None,
            "filter-songs": "songs",
            "filter-albums": "albums",
            "filter-artists": "artists",
            "filter-playlists": "playlists",
        }
        if event.pressed.id:
            self._filter_type = filter_map.get(event.pressed.id)
            # Re-run search if we have a query
            search_input = self.query_one("#search-input", Input)
            if search_input.value.strip():
                self.post_message(
                    self.SearchRequested(search_input.value.strip(), self._filter_type)
                )

    def set_results(self, results: SearchResults) -> None:
        """Display search results."""
        self._results = results
        track_list = self.query_one("#track-list", TrackList)
        results_table = self.query_one("#results-table", DataTable)

        # Show appropriate view based on filter
        if self._filter_type == "songs" or self._filter_type is None and results.tracks:
            track_list.display = True
            results_table.display = False
            track_list.set_tracks(results.tracks)
            self._current_items = results.tracks
            self.query_one("#results-header", Static).update(
                f"Results - {len(results.tracks)} songs"
            )
        else:
            track_list.display = False
            results_table.display = True
            results_table.clear()
            self._current_items = []

            if self._filter_type == "albums":
                for album in results.albums:
                    artists = ", ".join(a.name for a in album.artists)
                    results_table.add_row("Album", album.title[:40], artists[:30])
                    self._current_items.append(album)
                self.query_one("#results-header", Static).update(
                    f"Results - {len(results.albums)} albums"
                )
            elif self._filter_type == "artists":
                for artist in results.artists:
                    results_table.add_row(
                        "Artist", artist.name[:40], artist.subscribers or ""
                    )
                    self._current_items.append(artist)
                self.query_one("#results-header", Static).update(
                    f"Results - {len(results.artists)} artists"
                )
            elif self._filter_type == "playlists":
                for playlist in results.playlists:
                    results_table.add_row(
                        "Playlist",
                        playlist.title[:40],
                        f"{playlist.track_count} tracks",
                    )
                    self._current_items.append(playlist)
                self.query_one("#results-header", Static).update(
                    f"Results - {len(results.playlists)} playlists"
                )
            else:
                # Mixed results
                for track in results.tracks:
                    results_table.add_row("Song", track.title[:40], track.artist_names[:30])
                    self._current_items.append(track)
                for album in results.albums:
                    artists = ", ".join(a.name for a in album.artists)
                    results_table.add_row("Album", album.title[:40], artists[:30])
                    self._current_items.append(album)
                for artist in results.artists:
                    results_table.add_row("Artist", artist.name[:40], "")
                    self._current_items.append(artist)
                for playlist in results.playlists:
                    results_table.add_row(
                        "Playlist", playlist.title[:40], f"{playlist.track_count} tracks"
                    )
                    self._current_items.append(playlist)

                total = (
                    len(results.tracks)
                    + len(results.albums)
                    + len(results.artists)
                    + len(results.playlists)
                )
                self.query_one("#results-header", Static).update(
                    f"Results - {total} items"
                )

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        track_list = self.query_one("#track-list", TrackList)
        results_table = self.query_one("#results-table", DataTable)
        if track_list.display:
            track_list.action_cursor_down()
        else:
            results_table.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        track_list = self.query_one("#track-list", TrackList)
        results_table = self.query_one("#results-table", DataTable)
        if track_list.display:
            track_list.action_cursor_up()
        else:
            results_table.action_cursor_up()

    def action_select(self) -> None:
        """Select current item."""
        from squid.api.models import Track, Album, Artist, Playlist

        track_list = self.query_one("#track-list", TrackList)
        results_table = self.query_one("#results-table", DataTable)

        if track_list.display:
            track_list.action_select()
        elif results_table.cursor_row is not None:
            idx = results_table.cursor_row
            if idx < len(self._current_items):
                item = self._current_items[idx]
                if isinstance(item, Track):
                    self.post_message(self.TrackSelected(item))
                elif isinstance(item, Album):
                    self.post_message(self.AlbumSelected(item))
                elif isinstance(item, Artist):
                    self.post_message(self.ArtistSelected(item))
                elif isinstance(item, Playlist):
                    self.post_message(self.PlaylistSelected(item))

    def action_add_to_queue(self) -> None:
        """Add current track to queue."""
        track_list = self.query_one("#track-list", TrackList)
        if track_list.display:
            track_list.action_add_to_queue()

    def set_current_track(self, track_id: str | None) -> None:
        """Highlight currently playing track."""
        track_list = self.query_one("#track-list", TrackList)
        track_list.set_current(track_id)

    # TrackList and SearchView messages bubble naturally to the app

    def action_noop(self) -> None:
        """No-op for view switch key."""
        pass
