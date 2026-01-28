"""Main Textual application."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import structlog
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.widget import Widget
from textual.widgets import Footer, Header, Static

from squid.api import YouTubeMusicClient, Track, Album, Artist, Playlist
from squid.api.auth import AuthError
from squid.keybindings import Keybindings, DEFAULT_BINDINGS, CommandParser, Command
from squid.player import MPVBackend, PlayQueue, PlaybackState, PlayerState
from squid.player.state import RepeatMode
from squid.views import (
    LibraryTreeView,
    LibrarySortedView,
    QueueView,
    NowPlayingView,
    SearchView,
    SettingsView,
)
from squid.widgets import CommandLine, PlayBar

if TYPE_CHECKING:
    from squid.config import Config

log = structlog.get_logger()


class SquidApp(App):
    """Squid - YouTube Music TUI."""

    TITLE = "Squid"
    SUB_TITLE = "YouTube Music"
    CSS_PATH = "styles/app.tcss"
    ENABLE_COMMAND_PALETTE = False

    # Use terminal's ANSI colors instead of Textual's default theme
    ansi_color = True

    BINDINGS = [
        Binding("1", "view_1", "[Library]", key_display=" ", show=True),
        Binding("2", "view_2", "[All Tracks]", key_display=" ", show=True),
        Binding("3", "view_3", "[Queue]", key_display=" ", show=True),
        Binding("4", "view_4", "[Playing]", key_display=" ", show=True),
        Binding("5", "view_5", "[Search]", key_display=" ", show=True),
        Binding("6", "view_6", "[Settings]", key_display=" ", show=True),
        Binding("c", "play_pause", "Play/Pause", show=False),
        Binding("b", "next_track", "Next", show=False),
        Binding("z", "prev_track", "Previous", show=False),
        Binding("v", "stop", "Stop", show=False),
        Binding("+", "volume_up", "Vol+", show=False),
        Binding("=", "volume_up", "Vol+", show=False),
        Binding("-", "volume_down", "Vol-", show=False),
        Binding("m", "mute", "Mute", show=False),
        Binding("s", "toggle_shuffle", "Shuffle", show=False),
        Binding("r", "cycle_repeat", "Repeat", show=False),
        Binding("l", "seek_forward", "Seek+", show=False),
        Binding("h", "seek_backward", "Seek-", show=False),
        Binding(":", "command_mode", "Command", show=False),
        Binding("/", "search_mode", "Search", show=False),
        Binding("q", "quit", "[Quit]", key_display=" ", show=True),
    ]

    def __init__(self, config: Config, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.client: YouTubeMusicClient | None = None
        self.player: MPVBackend | None = None
        self.queue = PlayQueue()
        self.keybindings = Keybindings()
        self.command_parser = CommandParser()
        self._current_view = "library_tree"
        self._library_loaded = False
        self._all_tracks: list[Track] = []

        # View names for switching
        self._view_classes = {
            "library_tree": LibraryTreeView,
            "library_sorted": LibrarySortedView,
            "queue": QueueView,
            "now_playing": NowPlayingView,
            "search": SearchView,
            "settings": SettingsView,
        }

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Horizontal(id="content-row"):
            with Vertical(id="main-content"):
                # All views are created here, visibility controlled via display property
                yield LibraryTreeView(id="view-library_tree")
                yield LibrarySortedView(id="view-library_sorted")
                yield QueueView(id="view-queue")
                yield NowPlayingView(id="view-now_playing")
                yield SearchView(id="view-search")
                yield SettingsView(id="view-settings")
        yield PlayBar(id="play-bar")
        yield CommandLine(id="command-line")

    async def on_mount(self) -> None:
        """Initialize application on mount."""
        # Hide all views except the initial one
        for name in self._view_classes.keys():
            view = self.query_one(f"#view-{name}")
            view.display = (name == "library_tree")

        # Initialize client and player
        self._init_services()

        # Load library
        self._load_library()

    async def _switch_view(self, view_name: str) -> None:
        """Switch to a different view by showing/hiding."""
        # Hide all views
        for name in self._view_classes.keys():
            view = self.query_one(f"#view-{name}")
            view.display = (name == view_name)

        self._current_view = view_name

        # Focus the new view
        new_view = self.query_one(f"#view-{view_name}")
        new_view.focus()

    def _get_view(self, view_name: str) -> Widget | None:
        """Get a view instance by name."""
        try:
            return self.query_one(f"#view-{view_name}")
        except Exception:
            return None

    def _init_services(self) -> None:
        """Initialize API client and player."""
        try:
            self.client = YouTubeMusicClient(self.config)
            self.player = MPVBackend(initial_volume=self.config.default_volume)

            # Register player callbacks
            self.player.on_state_change(self._on_playback_state_change)
            self.player.on_track_end(self._on_track_end)

            log.info("Services initialized")
        except AuthError as e:
            log.error("Authentication required", error=str(e))
            self.notify("Authentication required. Run: squid --auth", severity="error")
        except Exception as e:
            log.error("Failed to initialize services", error=str(e))
            self.notify(f"Initialization error: {e}", severity="error")

    def _on_playback_state_change(self, state: PlaybackState) -> None:
        """Handle playback state changes."""
        import threading
        # MPV callbacks come from a different thread, but sometimes we're already in main thread
        if threading.current_thread() is threading.main_thread():
            self._update_ui_state(state)
        else:
            self.call_from_thread(self._update_ui_state, state)

    def _update_ui_state(self, state: PlaybackState) -> None:
        """Update UI with new playback state."""
        # Update play bar
        play_bar = self.query_one("#play-bar", PlayBar)
        play_bar.update_state(state)

        # Update current track in views
        track_id = state.current_track.id if state.current_track else None
        self._update_track_highlight(track_id)

        # Update now playing view if active
        if self._current_view == "now_playing":
            view = self._get_view("now_playing")
            if isinstance(view, NowPlayingView):
                view.update_state(state)

    def _update_track_highlight(self, track_id: str | None) -> None:
        """Update currently playing track highlight across views."""
        for view_name in ["library_tree", "library_sorted", "search"]:
            view = self._get_view(view_name)
            if view and hasattr(view, "set_current_track"):
                view.set_current_track(track_id)

    def _on_track_end(self) -> None:
        """Handle track end."""
        import threading
        if threading.current_thread() is threading.main_thread():
            self._advance_queue()
        else:
            self.call_from_thread(self._advance_queue)

    def _advance_queue(self) -> None:
        """Advance to next track in queue."""
        if not self.player:
            return

        state = self.player.state
        if state.repeat == RepeatMode.ONE:
            # Replay current track
            if self.queue.current:
                self._play_track(self.queue.current)
        else:
            next_track = self.queue.next()
            if next_track:
                self._play_track(next_track)
            elif state.repeat == RepeatMode.ALL and self.queue.length > 0:
                # Loop back to start
                self.queue.set_current(0)
                if self.queue.current:
                    self._play_track(self.queue.current)

        # Update queue view
        self._update_queue_view()

    @work(exclusive=True, thread=True)
    def _load_library(self) -> None:
        """Load library data in background."""
        if not self.client:
            return

        try:
            # Run async code in the worker thread
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                library = loop.run_until_complete(self.client.get_library_data())
            finally:
                loop.close()

            self.call_from_thread(self._on_library_loaded, library)
        except Exception as e:
            log.error("Failed to load library", error=str(e))
            self.call_from_thread(
                self.notify, f"Failed to load library: {e}", severity="error"
            )

    def _on_library_loaded(self, library) -> None:
        """Handle library loaded."""
        from squid.api.models import LibraryData

        if not isinstance(library, LibraryData):
            return

        self._library_loaded = True

        # Collect all tracks for sorted view
        self._all_tracks = []
        if library.liked_songs:
            self._all_tracks.extend(library.liked_songs.tracks)

        # Update views
        view = self._get_view("library_tree")
        if isinstance(view, LibraryTreeView):
            view.set_artists(library.artists)
            view.set_playlists(library.playlists)

        sorted_view = self._get_view("library_sorted")
        if isinstance(sorted_view, LibrarySortedView):
            sorted_view.set_tracks(self._all_tracks)

        settings_view = self._get_view("settings")
        if isinstance(settings_view, SettingsView):
            settings_view.update_settings(
                config_dir=str(self.config.config_dir),
                cache_dir=str(self.config.cache_dir),
                is_authenticated=self.client.auth.is_authenticated if self.client else False,
                default_volume=self.config.default_volume,
                cache_ttl=self.config.cache_ttl_hours,
                keybindings=self.keybindings,
            )

        log.info(
            "Library loaded",
            artists=len(library.artists),
            albums=len(library.albums),
            playlists=len(library.playlists),
        )

    def _update_queue_view(self) -> None:
        """Update the queue view display."""
        view = self._get_view("queue")
        if isinstance(view, QueueView):
            view.update_queue(self.queue.tracks, self.queue.current_index)

    # View switching actions
    async def action_view_1(self) -> None:
        """Switch to library tree view."""
        await self._switch_view("library_tree")

    async def action_view_2(self) -> None:
        """Switch to library sorted view."""
        await self._switch_view("library_sorted")

    async def action_view_3(self) -> None:
        """Switch to queue view."""
        self._update_queue_view()
        await self._switch_view("queue")

    async def action_view_4(self) -> None:
        """Switch to now playing view."""
        await self._switch_view("now_playing")
        if self.player:
            view = self._get_view("now_playing")
            if isinstance(view, NowPlayingView):
                view.update_state(self.player.state)

    async def action_view_5(self) -> None:
        """Switch to search view."""
        await self._switch_view("search")

    async def action_view_6(self) -> None:
        """Switch to settings view."""
        await self._switch_view("settings")

    # Playback actions
    def action_play_pause(self) -> None:
        """Toggle play/pause."""
        if self.player:
            self.player.toggle_pause()

    def action_stop(self) -> None:
        """Stop playback."""
        if self.player:
            self.player.stop()

    def action_next_track(self) -> None:
        """Skip to next track."""
        self._advance_queue()

    def action_prev_track(self) -> None:
        """Go to previous track."""
        if not self.player:
            return

        prev_track = self.queue.previous()
        if prev_track:
            self._play_track(prev_track)
            self._update_queue_view()

    def action_seek_forward(self) -> None:
        """Seek forward 10 seconds."""
        if self.player:
            self.player.seek(10)

    def action_seek_backward(self) -> None:
        """Seek backward 10 seconds."""
        if self.player:
            self.player.seek(-10)

    def action_volume_up(self) -> None:
        """Increase volume."""
        if self.player:
            self.player.adjust_volume(5)

    def action_volume_down(self) -> None:
        """Decrease volume."""
        if self.player:
            self.player.adjust_volume(-5)

    def action_mute(self) -> None:
        """Toggle mute."""
        if self.player:
            self.player.mute()

    def action_toggle_shuffle(self) -> None:
        """Toggle shuffle mode."""
        if self.player:
            new_shuffle = not self.player.state.shuffle
            self.queue.shuffle(new_shuffle)
            self.player.state.shuffle = new_shuffle
            self.notify(f"Shuffle {'on' if new_shuffle else 'off'}")
            self._update_queue_view()

    def action_cycle_repeat(self) -> None:
        """Cycle repeat mode."""
        if self.player:
            mode = self.player.cycle_repeat()
            mode_names = {
                RepeatMode.OFF: "off",
                RepeatMode.ALL: "all",
                RepeatMode.ONE: "one",
            }
            self.notify(f"Repeat: {mode_names[mode]}")

    # Command mode
    def action_command_mode(self) -> None:
        """Enter command mode."""
        command_line = self.query_one("#command-line", CommandLine)
        command_line.activate("command")

    def action_search_mode(self) -> None:
        """Enter search mode."""
        command_line = self.query_one("#command-line", CommandLine)
        command_line.activate("search")

    def on_command_line_command_submitted(
        self, event: CommandLine.CommandSubmitted
    ) -> None:
        """Handle command submission."""
        if event.mode == "search":
            self._do_search(event.command)
        else:
            self._execute_command(event.command)

    def _execute_command(self, command_str: str) -> None:
        """Execute a command."""
        cmd = self.command_parser.parse(command_str)
        if not cmd:
            return

        if cmd.name == "quit":
            self.exit()
        elif cmd.name == "volume":
            if cmd.arg:
                try:
                    vol = int(cmd.arg)
                    if self.player:
                        self.player.set_volume(vol)
                except ValueError:
                    self.notify("Invalid volume", severity="error")
        elif cmd.name == "seek":
            if cmd.arg:
                try:
                    secs = int(cmd.arg)
                    if self.player:
                        self.player.seek(secs, relative=False)
                except ValueError:
                    self.notify("Invalid position", severity="error")
        elif cmd.name == "shuffle":
            self.action_toggle_shuffle()
        elif cmd.name == "repeat":
            self.action_cycle_repeat()
        elif cmd.name == "clear":
            self.queue.clear()
            self._update_queue_view()
            self.notify("Queue cleared")
        elif cmd.name == "refresh":
            self._load_library()
            self.notify("Refreshing library...")
        elif cmd.name == "cache":
            if cmd.arg == "clear":
                asyncio.create_task(self._clear_cache())
        elif cmd.name == "help":
            asyncio.create_task(self.action_view_7())
        else:
            self.notify(f"Unknown command: {cmd.name}", severity="warning")

    async def _clear_cache(self) -> None:
        """Clear the API cache."""
        if self.client:
            await self.client.clear_cache()
            self.notify("Cache cleared")

    @work(exclusive=True, thread=True)
    def _do_search(self, query: str) -> None:
        """Perform search."""
        if not self.client:
            return

        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(self.client.search(query))
            finally:
                loop.close()

            self.call_from_thread(self._on_search_results, results)
        except Exception as e:
            log.error("Search failed", error=str(e))
            self.call_from_thread(self.notify, f"Search failed: {e}", severity="error")

    def _on_search_results(self, results) -> None:
        """Handle search results."""
        from squid.api.models import SearchResults

        if not isinstance(results, SearchResults):
            return

        view = self._get_view("search")
        if isinstance(view, SearchView):
            view.set_results(results)

        # Switch to search view
        asyncio.create_task(self.action_view_6())

    # Message handlers from views
    def on_track_list_track_selected(self, event) -> None:
        """Handle track selection from any view."""
        track = event.track
        log.info("Track selected", title=track.title, id=track.id)
        # Replace queue with current context and play
        self.queue.replace([track], 0)
        if self.player:
            self._play_track(track)
        self._update_queue_view()

    @work(exclusive=True, thread=True)
    def _play_track(self, track: Track) -> None:
        """Play a track in a worker thread."""
        if not self.player:
            log.error("_play_track: No player available")
            return
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.player.play(track))
            finally:
                loop.close()
        except Exception as e:
            log.error("_play_track failed", title=track.title, error=str(e))

    def on_track_list_track_add_to_queue(self, event) -> None:
        """Handle add to queue."""
        self.queue.add(event.track)
        self.notify(f"Added: {event.track.title}")
        self._update_queue_view()

    def on_artist_tree_artist_selected(self, event) -> None:
        """Handle artist selection."""
        self._fetch_artist(event.artist.id)

    def on_artist_tree_album_selected(self, event) -> None:
        """Handle album selection."""
        self._fetch_album(event.album.id)

    def on_artist_tree_playlist_selected(self, event) -> None:
        """Handle playlist selection from library tree."""
        self._fetch_playlist_for_library(event.playlist.id)

    @work(exclusive=True, thread=True)
    def _fetch_playlist_for_library(self, playlist_id: str) -> None:
        """Fetch playlist and display tracks in library view."""
        if not self.client:
            return

        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                playlist = loop.run_until_complete(self.client.get_playlist(playlist_id))
            finally:
                loop.close()

            self.call_from_thread(self._set_library_tracks, playlist.tracks)
        except Exception as e:
            log.error("Failed to fetch playlist", error=str(e))

    @work(exclusive=True, thread=True)
    def _fetch_artist(self, artist_id: str) -> None:
        """Fetch artist details."""
        if not self.client:
            return

        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                artist = loop.run_until_complete(self.client.get_artist(artist_id))
            finally:
                loop.close()

            # Get all tracks from artist's albums
            tracks = []
            for album in artist.albums:
                tracks.extend(album.tracks)

            self.call_from_thread(self._set_library_tracks, tracks)
        except Exception as e:
            log.error("Failed to fetch artist", error=str(e))

    @work(exclusive=True, thread=True)
    def _fetch_album(self, album_id: str) -> None:
        """Fetch album details."""
        if not self.client:
            return

        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                album = loop.run_until_complete(self.client.get_album(album_id))
            finally:
                loop.close()

            self.call_from_thread(self._set_library_tracks, album.tracks)
        except Exception as e:
            log.error("Failed to fetch album", error=str(e))

    def _set_library_tracks(self, tracks: list[Track]) -> None:
        """Set tracks in library view."""
        view = self._get_view("library_tree")
        if isinstance(view, LibraryTreeView):
            view.set_tracks(tracks)

    def on_search_view_search_requested(self, event) -> None:
        """Handle search request."""
        self._do_search(event.query)

    def on_queue_view_queue_track_selected(self, event) -> None:
        """Handle queue track selection."""
        self.queue.set_current(event.index)
        if self.queue.current and self.player:
            self._play_track(self.queue.current)
        self._update_queue_view()

    def on_queue_view_queue_track_removed(self, event) -> None:
        """Handle queue track removal."""
        self.queue.remove(event.index)
        self._update_queue_view()

    def on_queue_view_queue_track_moved(self, event) -> None:
        """Handle queue track move."""
        self.queue.move(event.from_index, event.to_index)
        self._update_queue_view()

    def on_queue_view_queue_cleared(self, event) -> None:
        """Handle queue clear."""
        self.queue.clear()
        self._update_queue_view()

    # PlayBar message handlers
    def on_play_bar_play_pause_clicked(self, event: PlayBar.PlayPauseClicked) -> None:
        """Handle play/pause button click."""
        self.action_play_pause()

    def on_play_bar_next_clicked(self, event: PlayBar.NextClicked) -> None:
        """Handle next button click."""
        self.action_next_track()

    def on_play_bar_previous_clicked(self, event: PlayBar.PreviousClicked) -> None:
        """Handle previous button click."""
        self.action_prev_track()

    def on_play_bar_seek_requested(self, event: PlayBar.SeekRequested) -> None:
        """Handle seek request from progress bar click."""
        if self.player:
            self.player.seek_percent(event.percent)

    def on_play_bar_volume_changed(self, event: PlayBar.VolumeChanged) -> None:
        """Handle volume change from PlayBar."""
        if self.player:
            self.player.set_volume(event.volume)

    def on_settings_view_cache_cleared(self, event) -> None:
        """Handle cache clear."""
        asyncio.create_task(self._clear_cache())

    def on_settings_view_auth_refresh(self, event) -> None:
        """Handle auth refresh."""
        self.notify("Please run 'squid --auth' in terminal to re-authenticate")

    async def on_unmount(self) -> None:
        """Clean up on exit."""
        if self.player:
            self.player.close()
        if self.client:
            await self.client.close()

        # Save queue
        self.queue.save(self.config.queue_path)
