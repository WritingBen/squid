"""Playbar widget with transport controls, scrubbing, and volume."""

from __future__ import annotations

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from squid.player.state import PlaybackState, PlayerState


class PlayBar(Widget):
    """Transport controls, scrubbable progress bar, and volume control."""

    class PlayPauseClicked(Message):
        """Play/pause button clicked."""
        pass

    class NextClicked(Message):
        """Next track button clicked."""
        pass

    class PreviousClicked(Message):
        """Previous track button clicked."""
        pass

    class SeekRequested(Message):
        """Seek to percentage requested."""
        def __init__(self, percent: float) -> None:
            super().__init__()
            self.percent = percent

    class VolumeChanged(Message):
        """Volume changed via click on volume bar."""
        def __init__(self, volume: int) -> None:
            super().__init__()
            self.volume = volume

    DEFAULT_CSS = """
    PlayBar {
        width: 100%;
        height: 3;
        background: $surface;
        layout: vertical;
    }

    PlayBar Static {
        width: 100%;
        height: 1;
    }
    """

    playback_state: reactive[PlaybackState] = reactive(PlaybackState)

    # Track bar geometry for click detection
    _bar_start_x: int = 0
    _bar_width: int = 0
    _vol_start_x: int = 0
    _vol_width: int = 10

    # Button positions for click detection
    _prev_start: int = 1
    _prev_end: int = 5
    _play_start: int = 5
    _play_end: int = 9
    _next_start: int = 9
    _next_end: int = 13

    def compose(self) -> ComposeResult:
        yield Static("", id="row-top", classes="playbar-row")
        yield Static("", id="row-middle", classes="playbar-row")
        yield Static("", id="row-bottom", classes="playbar-row")

    def on_mount(self) -> None:
        """Initialize display after mount."""
        self._update_display(self.playback_state)

    def on_mount(self) -> None:
        """Initialize display after mount."""
        self._update_display(self.playback_state)

    def on_resize(self, event: events.Resize) -> None:
        """Recalculate on resize."""
        self._update_display(self.playback_state)

    def watch_playback_state(self, state: PlaybackState) -> None:
        """Update display when playback state changes."""
        self._update_display(state)

    def _update_display(self, state: PlaybackState) -> None:
        """Render all three rows of the playbar."""
        width = self.size.width
        if width < 40:
            return

        # Fixed layout constants
        transport_box_width = 14  # ╭────────────╮
        vol_box_width = 16  # ╭──────────────╮
        progress_area_width = width - transport_box_width - vol_box_width

        # Time label widths (fixed format with padding)
        time_label_width = 6  # " 0:00 " to " 9:59 " or truncated

        # Progress bar width (fill remaining space between time labels)
        self._bar_width = max(10, progress_area_width - (time_label_width * 2))

        # Volume bar is always 10 chars
        self._vol_width = 10

        # Calculate click detection positions (from left edge of widget)
        # Transport content: │ (1) + space (1) + |< (2) + spaces (2) + icon (2) + spaces (2) + >| (2) + space (1) + │ (1) = 14
        # Button positions within the 14-char transport box:
        self._prev_start = 2   # |< starts at position 2
        self._prev_end = 4     # |< ends at position 4
        self._play_start = 6   # play icon starts at position 6
        self._play_end = 8     # play icon ends at position 8
        self._next_start = 10  # >| starts at position 10
        self._next_end = 12    # >| ends at position 12

        # Progress bar starts after transport box + position time label
        self._bar_start_x = transport_box_width + time_label_width

        # Volume bar position: count from right edge
        # From right: │ (1) + vol_bar (10) + "Vol " (4) + │ (1) = 16 chars total
        # Volume bar starts 11 chars from right edge (after "Vol " and before final │)
        self._vol_start_x = width - 1 - self._vol_width  # width - 11

        # Progress bar calculation
        progress = state.progress_percent
        bar_inner_width = self._bar_width - 1  # Reserve 1 for playhead
        playhead_pos = int((progress / 100) * bar_inner_width)
        playhead_pos = max(0, min(bar_inner_width, playhead_pos))

        # Volume bar calculation
        vol_filled = int((state.volume / 100) * self._vol_width)
        vol_empty = self._vol_width - vol_filled

        # Play/pause icon
        play_icon = "||" if state.state == PlayerState.PLAYING else "> "

        # Format time labels with fixed width
        pos_label = f" {state.position_str} ".ljust(time_label_width)[:time_label_width]
        dur_label = f" {state.duration_str} ".ljust(time_label_width)[:time_label_width]

        # Build top row
        top = Text()
        top.append("╭────────────╮", style="bright_black")
        top.append(" " * progress_area_width, style="default")
        top.append("╭──────────────╮", style="bright_black")
        self.query_one("#row-top", Static).update(top)

        # Build middle row (tracking positions for click detection)
        mid = Text()
        # Transport section: exactly 14 chars to match box
        # │ (1) + space (1) + |< (2) + space (2) + icon (2) + space (2) + >| (2) + space (1) + │ (1) = 14
        mid.append("│ ", style="bright_black")
        mid.append("|<", style="bold")
        mid.append("  ", style="default")
        mid.append(play_icon, style="bold")
        mid.append("  ", style="default")
        mid.append(">|", style="bold")
        mid.append(" │", style="bright_black")

        # Position time label
        mid.append(pos_label, style="bright_black")

        # Progress bar
        mid.append("=" * playhead_pos, style="cyan")
        mid.append("●", style="bright_white")
        mid.append("-" * (self._bar_width - playhead_pos - 1), style="cyan")

        # Duration time label
        mid.append(dur_label, style="bright_black")

        # Volume section: exactly 16 chars to match box
        # │ (1) + Vol (3) + space (1) + volume_bar (10) + │ (1) = 16
        mid.append("│", style="bright_black")
        mid.append("Vol ", style="bright_black")
        mid.append("█" * vol_filled, style="magenta")
        mid.append("░" * vol_empty, style="bright_black")
        mid.append("│", style="bright_black")
        self.query_one("#row-middle", Static).update(mid)

        # Build bottom row
        bot = Text()
        bot.append("╰────────────╯", style="bright_black")
        bot.append(" " * progress_area_width, style="default")
        bot.append("╰──────────────╯", style="bright_black")
        self.query_one("#row-bottom", Static).update(bot)

    def on_mouse_down(self, event: events.MouseDown) -> None:
        """Handle clicks on buttons, progress bar, or volume bar."""
        # Convert screen coordinates to widget-relative coordinates
        click_x = event.screen_x - self.region.x
        click_y = event.screen_y - self.region.y

        # Only handle clicks on the middle row
        if click_y != 1:
            return

        # Check transport buttons
        if self._prev_start <= click_x < self._prev_end:
            self.post_message(self.PreviousClicked())
            return
        elif self._play_start <= click_x < self._play_end:
            self.post_message(self.PlayPauseClicked())
            return
        elif self._next_start <= click_x < self._next_end:
            self.post_message(self.NextClicked())
            return

        # Check progress bar
        bar_start = self._bar_start_x
        bar_end = bar_start + self._bar_width
        if bar_start <= click_x < bar_end and self._bar_width > 0:
            relative_x = click_x - bar_start
            percent = (relative_x / self._bar_width) * 100
            percent = max(0, min(100, percent))
            self.post_message(self.SeekRequested(percent))
            return

        # Check volume bar
        vol_start = self._vol_start_x
        vol_end = vol_start + self._vol_width
        if vol_start <= click_x < vol_end and self._vol_width > 0:
            relative_x = click_x - vol_start
            volume = int((relative_x / self._vol_width) * 100)
            volume = max(0, min(100, volume))
            self.post_message(self.VolumeChanged(volume))

    def update_state(self, state: PlaybackState) -> None:
        """Public method to update playback state."""
        self.playback_state = state
        self._update_display(state)
