"""Queue view (View 4)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static, DataTable
from textual.binding import Binding

if TYPE_CHECKING:
    from squid.api.models import Track
    from squid.player.queue import PlayQueue


class QueueView(Widget):
    """View 4: Play queue with manipulation."""

    BINDINGS = [
        Binding("3", "noop", "[Queue]", key_display=" ", show=True),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("J", "move_down", "Move down", show=False),
        Binding("K", "move_up", "Move up", show=False),
        Binding("d", "remove", "Remove", show=False),
        Binding("D", "clear", "Clear", show=False),
        Binding("enter", "play", "Play", show=False),
        Binding("g", "scroll_home", "Top", show=False),
        Binding("G", "scroll_end", "Bottom", show=False),
    ]

    DEFAULT_CSS = """
    QueueView {
        layout: vertical;
        width: 100%;
        height: 100%;
    }

    QueueView .pane-header {
        height: 1;
        background: ansi_blue;
        color: ansi_white;
        padding: 0 1;
    }

    QueueView .queue-info {
        height: 1;
        background: $surface;
        color: ansi_bright_black;
        padding: 0 1;
    }

    QueueView DataTable {
        height: 1fr;
    }
    """

    class QueueTrackSelected(Message):
        """Track in queue was selected for playback."""

        def __init__(self, index: int) -> None:
            super().__init__()
            self.index = index

    class QueueTrackRemoved(Message):
        """Track was removed from queue."""

        def __init__(self, index: int) -> None:
            super().__init__()
            self.index = index

    class QueueTrackMoved(Message):
        """Track was moved in queue."""

        def __init__(self, from_index: int, to_index: int) -> None:
            super().__init__()
            self.from_index = from_index
            self.to_index = to_index

    class QueueCleared(Message):
        """Queue was cleared."""

        pass

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._tracks: list[Track] = []
        self._current_index: int = -1

    def compose(self) -> ComposeResult:
        yield Static("Play Queue", classes="pane-header")
        yield Static("0 tracks", id="queue-info", classes="queue-info")
        table = DataTable(id="queue-table", cursor_type="row")
        table.add_columns("#", "Title", "Artist", "Album", "Duration")
        yield table

    def update_queue(self, tracks: list[Track], current_index: int) -> None:
        """Update queue display."""
        self._tracks = tracks
        self._current_index = current_index
        self._refresh_table()

    def _refresh_table(self) -> None:
        """Refresh the queue table."""
        table = self.query_one("#queue-table", DataTable)
        table.clear()

        total_duration = sum(t.duration_seconds for t in self._tracks)
        minutes = total_duration // 60

        self.query_one("#queue-info", Static).update(
            f"{len(self._tracks)} tracks, {minutes} minutes"
        )

        for i, track in enumerate(self._tracks):
            # Mark current track
            marker = ">" if i == self._current_index else " "
            table.add_row(
                f"{marker}{i + 1}",
                track.title[:40],
                track.artist_names[:25],
                (track.album.title if track.album else "")[:20],
                track.duration_str,
                key=str(i),
            )

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        self.query_one("#queue-table", DataTable).action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        self.query_one("#queue-table", DataTable).action_cursor_up()

    def action_scroll_home(self) -> None:
        """Scroll to top."""
        self.query_one("#queue-table", DataTable).action_scroll_home()

    def action_scroll_end(self) -> None:
        """Scroll to bottom."""
        self.query_one("#queue-table", DataTable).action_scroll_end()

    def action_play(self) -> None:
        """Play selected track."""
        table = self.query_one("#queue-table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self._tracks):
            self.post_message(self.QueueTrackSelected(table.cursor_row))

    def action_remove(self) -> None:
        """Remove selected track from queue."""
        table = self.query_one("#queue-table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self._tracks):
            self.post_message(self.QueueTrackRemoved(table.cursor_row))

    def action_clear(self) -> None:
        """Clear the queue."""
        self.post_message(self.QueueCleared())

    def action_move_up(self) -> None:
        """Move selected track up in queue."""
        table = self.query_one("#queue-table", DataTable)
        if table.cursor_row is not None and table.cursor_row > 0:
            self.post_message(
                self.QueueTrackMoved(table.cursor_row, table.cursor_row - 1)
            )

    def action_move_down(self) -> None:
        """Move selected track down in queue."""
        table = self.query_one("#queue-table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self._tracks) - 1:
            self.post_message(
                self.QueueTrackMoved(table.cursor_row, table.cursor_row + 1)
            )

    # QueueView messages bubble naturally to the app

    def action_noop(self) -> None:
        """No-op for view switch key."""
        pass
