"""Artist/album tree widget."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Tree
from textual.widgets.tree import TreeNode
from textual.binding import Binding

if TYPE_CHECKING:
    from squid.api.models import Artist, Album, Playlist


class ArtistTree(Widget):
    """Tree view of artists and albums."""

    DEFAULT_CSS = """
    ArtistTree {
        width: 100%;
        height: 100%;
        background: ansi_default;
    }

    ArtistTree Tree {
        width: 100%;
        height: 100%;
        background: ansi_default;
    }
    """

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("h", "collapse", "Collapse", show=False),
        Binding("l", "expand", "Expand", show=False),
        Binding("enter", "select", "Select", show=False),
    ]

    class ArtistSelected(Message):
        """Artist node was selected."""

        def __init__(self, artist: Artist) -> None:
            super().__init__()
            self.artist = artist

    class AlbumSelected(Message):
        """Album node was selected."""

        def __init__(self, album: Album, artist: Artist) -> None:
            super().__init__()
            self.album = album
            self.artist = artist

    class PlaylistSelected(Message):
        """Playlist node was selected."""

        def __init__(self, playlist: Playlist) -> None:
            super().__init__()
            self.playlist = playlist

    artists: reactive[list[Artist]] = reactive(list, always_update=True)
    playlists: reactive[list[Playlist]] = reactive(list, always_update=True)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._artists: list[Artist] = []
        self._playlists: list[Playlist] = []
        self._node_data: dict[str, tuple[str, Artist | Album | Playlist, Artist | None]] = {}

    def compose(self) -> ComposeResult:
        yield Tree("Library", id="artist-tree")

    def watch_artists(self, artists: list[Artist]) -> None:
        """Update tree when artists change."""
        self._artists = artists
        self._refresh_tree()

    def watch_playlists(self, playlists: list[Playlist]) -> None:
        """Update tree when playlists change."""
        self._playlists = playlists
        self._refresh_tree()

    def _refresh_tree(self) -> None:
        """Refresh the tree view."""
        tree = self.query_one("#artist-tree", Tree)
        tree.clear()
        self._node_data.clear()

        # Ensure root is expanded
        tree.root.expand()

        # Add Playlists section
        if self._playlists:
            playlists_node = tree.root.add("Playlists")
            for playlist in self._playlists:
                # Playlists are leaf nodes - they open in right panel, don't expand
                playlist_node = playlists_node.add_leaf(f"  {playlist.title}")
                node_id = str(id(playlist_node))
                self._node_data[node_id] = ("playlist", playlist, None)
                playlist_node.data = node_id
            # Expand after adding children
            playlists_node.expand()

        # Add Artists section
        if self._artists:
            artists_node = tree.root.add("Artists", expand=False)
            for artist in self._artists:
                # Artists expand to show albums
                artist_node = artists_node.add(f"  {artist.name}")
                node_id = str(id(artist_node))
                self._node_data[node_id] = ("artist", artist, None)
                artist_node.data = node_id

                for album in artist.albums:
                    # Albums are leaf nodes - they open in right panel, don't expand
                    album_node = artist_node.add_leaf(f"    {album.title}")
                    album_node_id = str(id(album_node))
                    self._node_data[album_node_id] = ("album", album, artist)
                    album_node.data = album_node_id

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        tree = self.query_one("#artist-tree", Tree)
        tree.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        tree = self.query_one("#artist-tree", Tree)
        tree.action_cursor_up()

    def action_collapse(self) -> None:
        """Collapse current node."""
        tree = self.query_one("#artist-tree", Tree)
        if tree.cursor_node:
            tree.cursor_node.collapse()

    def action_expand(self) -> None:
        """Expand current node."""
        tree = self.query_one("#artist-tree", Tree)
        if tree.cursor_node:
            tree.cursor_node.expand()

    def action_select(self) -> None:
        """Select current node (keyboard Enter)."""
        tree = self.query_one("#artist-tree", Tree)
        node = tree.cursor_node
        self._select_node(node)

    def _select_node(self, node) -> None:
        """Process node selection."""
        if node and node.data:
            node_id = node.data
            if node_id in self._node_data:
                node_type, item, parent_artist = self._node_data[node_id]
                if node_type == "artist":
                    self.post_message(self.ArtistSelected(item))
                elif node_type == "album" and parent_artist:
                    self.post_message(self.AlbumSelected(item, parent_artist))
                elif node_type == "playlist":
                    self.post_message(self.PlaylistSelected(item))

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection (click or enter on tree)."""
        self._select_node(event.node)

    def set_artists(self, artists: list[Artist]) -> None:
        """Set artists (public API)."""
        self.artists = artists

    def set_playlists(self, playlists: list[Playlist]) -> None:
        """Set playlists (public API)."""
        self.playlists = playlists
