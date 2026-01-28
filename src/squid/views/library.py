"""Library views (Views 1 & 2)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Static, Label
from textual.binding import Binding

from squid.widgets.artist_tree import ArtistTree
from squid.widgets.track_list import TrackList
from squid.widgets.splitter import VerticalSplitter

if TYPE_CHECKING:
    from squid.api.models import Artist, Album, Track, Playlist


class LibraryTreeView(Widget):
    """View 1: Library artist/album tree."""

    BINDINGS = [
        Binding("1", "noop", "[Library]", key_display=" ", show=True),
    ]

    DEFAULT_CSS = """
    LibraryTreeView {
        layout: horizontal;
        width: 100%;
        height: 100%;
        background: ansi_default;
    }

    LibraryTreeView .library-tree-pane {
        height: 100%;
        background: ansi_default;
    }

    LibraryTreeView .library-tracks-pane {
        height: 100%;
        background: ansi_default;
    }

    LibraryTreeView .pane-header {
        height: 1;
        background: ansi_blue;
        color: ansi_white;
        padding: 0 1;
    }

    LibraryTreeView VerticalSplitter {
        width: 1;
        height: 100%;
    }
    """

    # Pane width ratio (0.0 to 1.0) - left pane takes this fraction
    _left_pane_ratio: float = 0.40

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._artists: list[Artist] = []
        self._current_tracks: list[Track] = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(classes="library-tree-pane", id="left-pane"):
                yield Static("Artists / Albums", classes="pane-header")
                yield ArtistTree(id="artist-tree")
            yield VerticalSplitter(id="pane-splitter")
            with Vertical(classes="library-tracks-pane", id="right-pane"):
                yield Static("Tracks", classes="pane-header")
                yield TrackList(id="track-list")

    def on_mount(self) -> None:
        """Set initial pane widths on mount."""
        self._apply_pane_widths()

    def _apply_pane_widths(self) -> None:
        """Apply current pane width ratio to the panes."""
        left_pane = self.query_one("#left-pane", Vertical)
        right_pane = self.query_one("#right-pane", Vertical)

        # Calculate widths accounting for 1-char splitter
        total_width = self.size.width - 1
        left_width = max(10, int(total_width * self._left_pane_ratio))
        right_width = max(10, total_width - left_width)

        left_pane.styles.width = left_width
        right_pane.styles.width = right_width

    def on_resize(self, event) -> None:
        """Reapply pane widths when view is resized."""
        self._apply_pane_widths()

    def on_vertical_splitter_dragged(self, event: VerticalSplitter.Dragged) -> None:
        """Handle splitter drag to resize panes."""
        # Calculate new ratio based on delta
        total_width = self.size.width - 1
        if total_width <= 0:
            return

        # Adjust ratio based on pixel movement
        delta_ratio = event.delta_x / total_width
        new_ratio = self._left_pane_ratio + delta_ratio

        # Clamp to reasonable bounds (20% to 80%)
        new_ratio = max(0.20, min(0.80, new_ratio))

        if new_ratio != self._left_pane_ratio:
            self._left_pane_ratio = new_ratio
            self._apply_pane_widths()

    def set_artists(self, artists: list[Artist]) -> None:
        """Set library artists."""
        self._artists = artists
        tree = self.query_one("#artist-tree", ArtistTree)
        tree.set_artists(artists)

    def set_playlists(self, playlists: list[Playlist]) -> None:
        """Set library playlists."""
        tree = self.query_one("#artist-tree", ArtistTree)
        tree.set_playlists(playlists)

    def set_tracks(self, tracks: list[Track]) -> None:
        """Set tracks for selected artist/album."""
        self._current_tracks = tracks
        track_list = self.query_one("#track-list", TrackList)
        track_list.set_tracks(tracks)

    def set_current_track(self, track_id: str | None) -> None:
        """Highlight currently playing track."""
        track_list = self.query_one("#track-list", TrackList)
        track_list.set_current(track_id)

    def on_artist_tree_artist_selected(self, event: ArtistTree.ArtistSelected) -> None:
        """Handle artist selection."""
        # App will fetch artist details and call set_tracks
        self.app.post_message(event)

    def on_artist_tree_album_selected(self, event: ArtistTree.AlbumSelected) -> None:
        """Handle album selection."""
        # App will fetch album details and call set_tracks
        self.app.post_message(event)

    def on_artist_tree_playlist_selected(self, event: ArtistTree.PlaylistSelected) -> None:
        """Handle playlist selection."""
        # App will fetch playlist details and call set_tracks
        self.app.post_message(event)

    # TrackList messages bubble naturally to the app - no explicit forwarding needed

    def action_noop(self) -> None:
        """No-op for view switch key."""
        pass


class LibrarySortedView(Widget):
    """View 2: Library flat sorted track list."""

    BINDINGS = [
        Binding("2", "noop", "[All Tracks]", key_display=" ", show=True),
    ]

    DEFAULT_CSS = """
    LibrarySortedView {
        layout: vertical;
        width: 100%;
        height: 100%;
        background: ansi_default;
    }

    LibrarySortedView .pane-header {
        height: 1;
        background: ansi_blue;
        color: ansi_white;
        padding: 0 1;
    }

    LibrarySortedView .sort-info {
        height: 1;
        background: ansi_default;
        color: ansi_bright_black;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._tracks: list[Track] = []
        self._sort_by: str = "artist"
        self._is_mounted = False

    def compose(self) -> ComposeResult:
        yield Static("Library - All Tracks", classes="pane-header")
        yield Static("Sorted by: artist", id="sort-info", classes="sort-info")
        yield TrackList(id="track-list")

    def on_mount(self) -> None:
        """Handle screen mount - apply sort if data is available."""
        self._is_mounted = True
        if self._tracks:
            self._apply_sort()

    def set_tracks(self, tracks: list[Track]) -> None:
        """Set all library tracks."""
        self._tracks = tracks
        if self._is_mounted:
            self._apply_sort()

    def _apply_sort(self) -> None:
        """Apply current sort to tracks."""
        sorted_tracks = self._tracks.copy()

        if self._sort_by == "artist":
            sorted_tracks.sort(key=lambda t: (t.artist_names.lower(), t.title.lower()))
        elif self._sort_by == "album":
            sorted_tracks.sort(key=lambda t: ((t.album.title if t.album else "").lower(), t.title.lower()))
        elif self._sort_by == "title":
            sorted_tracks.sort(key=lambda t: t.title.lower())
        elif self._sort_by == "duration":
            sorted_tracks.sort(key=lambda t: t.duration_seconds)

        track_list = self.query_one("#track-list", TrackList)
        track_list.set_tracks(sorted_tracks)
        self.query_one("#sort-info", Static).update(f"Sorted by: {self._sort_by}")

    def set_sort(self, sort_by: str) -> None:
        """Set sort order."""
        if sort_by in ("artist", "album", "title", "duration"):
            self._sort_by = sort_by
            self._apply_sort()

    def set_current_track(self, track_id: str | None) -> None:
        """Highlight currently playing track."""
        track_list = self.query_one("#track-list", TrackList)
        track_list.set_current(track_id)

    # TrackList messages bubble naturally to the app - no explicit forwarding needed

    def action_noop(self) -> None:
        """No-op for view switch key."""
        pass
