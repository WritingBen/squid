"""Scrollable track list widget."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable
from textual.binding import Binding
from textual import events

from squid.widgets.resizable_header import ResizableHeader, ColumnDef

if TYPE_CHECKING:
    from squid.api.models import Track


class TrackList(Widget):
    """Scrollable list of tracks with CMUS-style navigation."""

    DEFAULT_CSS = """
    TrackList {
        width: 100%;
        height: 100%;
        background: ansi_default;
        layout: vertical;
    }

    TrackList DataTable {
        width: 100%;
        height: 1fr;
        background: ansi_default;
    }

    TrackList ResizableHeader {
        height: 1;
    }
    """

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("g", "scroll_home", "Top", show=False),
        Binding("G", "scroll_end", "Bottom", show=False),
        # Note: Enter is handled by DataTable's RowSelected event
        Binding("a", "add_to_queue", "Add to queue", show=False),
    ]

    class TrackSelected(Message):
        """Track was selected for playback."""

        def __init__(self, track: Track, index: int) -> None:
            super().__init__()
            self.track = track
            self.index = index

    class TrackAddToQueue(Message):
        """Track should be added to queue."""

        def __init__(self, track: Track) -> None:
            super().__init__()
            self.track = track

    tracks: reactive[list[Track]] = reactive(list, always_update=True)
    current_track_id: reactive[str | None] = reactive(None)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._track_list: list[Track] = []
        self._sort_column: int | None = None
        self._sort_ascending: bool = True
        # Column definitions with default widths
        self._columns = [
            ColumnDef("#", 5, min_width=4, resizable=False),
            ColumnDef("Title", 25, min_width=10),
            ColumnDef("Artist", 15, min_width=8),
            ColumnDef("Album", 12, min_width=6),
            ColumnDef("Time", 7, min_width=5, resizable=False),
        ]

    def compose(self) -> ComposeResult:
        yield ResizableHeader(self._columns, id="track-header")
        table = DataTable(id="track-table", cursor_type="row", show_header=False)
        # Add columns with widths that include separator space
        # DataTable adds 1-char padding on each side, so reduce content width by 2
        cell_pad = 2
        for i, col in enumerate(self._columns):
            # Include separator width (1 char) for resizable columns (except last)
            sep_width = 1 if (i < len(self._columns) - 1 and col.resizable) else 0
            width = max(1, col.width + sep_width - cell_pad)
            table.add_column(col.name, width=width)
        yield table

    def watch_tracks(self, tracks: list[Track]) -> None:
        """Update table when tracks change."""
        self._track_list = tracks
        self._refresh_table()

    def watch_current_track_id(self, track_id: str | None) -> None:
        """Highlight currently playing track."""
        self._refresh_table()

    def _get_column_widths(self) -> tuple[int, int, int, int, int]:
        """Get current column widths from header (source of truth)."""
        try:
            header = self.query_one("#track-header", ResizableHeader)
            widths = header.get_column_widths()
            return tuple(widths)
        except Exception:
            # Fallback to default widths if header not mounted yet
            return tuple(col.width for col in self._columns)

    def _get_sorted_tracks(self) -> list[Track]:
        """Get tracks sorted by current sort column."""
        if self._sort_column is None:
            return self._track_list

        tracks = list(self._track_list)

        def get_sort_key(track: Track):
            if self._sort_column == 0:  # # (original order/index)
                return self._track_list.index(track) if track in self._track_list else 0
            elif self._sort_column == 1:  # Title
                return track.title.lower()
            elif self._sort_column == 2:  # Artist
                return track.artist_names.lower()
            elif self._sort_column == 3:  # Album
                return (track.album.title if track.album else "").lower()
            elif self._sort_column == 4:  # Time
                return track.duration_seconds
            return 0

        tracks.sort(key=get_sort_key, reverse=not self._sort_ascending)
        return tracks

    def _refresh_table(self) -> None:
        """Refresh the data table."""
        table = self.query_one("#track-table", DataTable)
        table.clear()

        # Get column widths
        num_w, title_w, artist_w, album_w, dur_w = self._get_column_widths()

        # Update DataTable column widths (include separator space in each column)
        # DataTable adds 1-char padding on each side of cells, so reduce content width by 2
        cell_pad = 2
        # Columns with separator after: Title, Artist, Album (add 1 for separator space)
        widths = [
            max(1, num_w - cell_pad),  # # (no separator after)
            max(1, title_w + 1 - cell_pad),  # Title + separator
            max(1, artist_w + 1 - cell_pad),  # Artist + separator
            max(1, album_w + 1 - cell_pad),  # Album + separator
            max(1, dur_w - cell_pad),  # Duration (no separator after)
        ]
        for i, col_key in enumerate(table.columns):
            col = table.columns[col_key]
            col.width = widths[i]

        # Get sorted tracks
        sorted_tracks = self._get_sorted_tracks()

        for i, track in enumerate(sorted_tracks):
            # Find original index for highlighting
            orig_idx = self._track_list.index(track) if track in self._track_list else i

            # Highlight current track
            num = f">{orig_idx + 1}" if track.id == self.current_track_id else f" {orig_idx + 1}"

            # Pad/truncate to column widths (include separator space for middle columns)
            num = num.ljust(num_w)[:num_w]
            # Add separator space (│) after Title, Artist, Album
            title = (track.title.ljust(title_w)[:title_w] + "│")
            artist = (track.artist_names.ljust(artist_w)[:artist_w] + "│")
            album_title = track.album.title if track.album else ""
            album = (album_title.ljust(album_w)[:album_w] + "│")
            dur = track.duration_str.ljust(dur_w)[:dur_w]

            table.add_row(
                num,
                title,
                artist,
                album,
                dur,
                key=f"{i}_{track.id}",
            )

    def on_resize(self, event: events.Resize) -> None:
        """Refresh table when widget resizes to recalculate column widths."""
        if self._track_list:
            self._refresh_table()

    def on_resizable_header_column_resized(self, event: ResizableHeader.ColumnResized) -> None:
        """Handle column resize from header."""
        if self._track_list:
            self._refresh_table()

    def on_resizable_header_column_clicked(self, event: ResizableHeader.ColumnClicked) -> None:
        """Handle column header click for sorting."""
        col_idx = event.column_index

        # Toggle sort direction if same column, otherwise set ascending
        if self._sort_column == col_idx:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_column = col_idx
            self._sort_ascending = True

        # Update header sort indicator
        header = self.query_one("#track-header", ResizableHeader)
        direction = "asc" if self._sort_ascending else "desc"
        header.set_sort_column(col_idx, direction)

        # Refresh table with new sort
        self._refresh_table()

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        table = self.query_one("#track-table", DataTable)
        table.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        table = self.query_one("#track-table", DataTable)
        table.action_cursor_up()

    def action_scroll_home(self) -> None:
        """Scroll to top."""
        table = self.query_one("#track-table", DataTable)
        table.action_scroll_home()

    def action_scroll_end(self) -> None:
        """Scroll to bottom."""
        table = self.query_one("#track-table", DataTable)
        table.action_scroll_end()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection (mouse click)."""
        self._select_row(event.cursor_row)

    def _select_row(self, row: int | None) -> None:
        """Select track at given row."""
        if row is not None and row < len(self._track_list):
            track = self._track_list[row]
            self.post_message(self.TrackSelected(track, row))

    def action_add_to_queue(self) -> None:
        """Add current track to queue."""
        table = self.query_one("#track-table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self._track_list):
            track = self._track_list[table.cursor_row]
            self.post_message(self.TrackAddToQueue(track))

    def set_tracks(self, tracks: list[Track]) -> None:
        """Set tracks (public API)."""
        self.tracks = tracks

    def set_current(self, track_id: str | None) -> None:
        """Set currently playing track."""
        self.current_track_id = track_id
