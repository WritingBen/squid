"""MPV audio backend."""

from __future__ import annotations

import asyncio
import threading
from typing import TYPE_CHECKING, Callable

import mpv
import structlog

from squid.player.state import PlaybackState, PlayerState, RepeatMode
from squid.player.stream import StreamExtractor, StreamError

if TYPE_CHECKING:
    from squid.api.models import Track

log = structlog.get_logger()


class MPVBackend:
    """MPV-based audio playback backend."""

    def __init__(self, initial_volume: int = 80) -> None:
        self._player: mpv.MPV | None = None
        self._stream_extractor = StreamExtractor()
        self._state = PlaybackState(volume=initial_volume)
        self._state_callbacks: list[Callable[[PlaybackState], None]] = []
        self._end_callbacks: list[Callable[[], None]] = []
        self._lock = threading.Lock()  # Use threading lock for cross-thread safety
        self._starting_playback = False  # Flag to prevent race condition

    def _init_player(self) -> mpv.MPV:
        """Initialize MPV player."""
        import locale
        # Fix locale for MPV (prevents "Non-C locale detected" warning/crash)
        locale.setlocale(locale.LC_NUMERIC, "C")

        player = mpv.MPV(
            video=False,
            ytdl=False,  # We use yt-dlp directly
            input_default_bindings=False,
            input_vo_keyboard=False,
            terminal=False,  # Disable terminal output (conflicts with TUI)
        )
        player.volume = self._state.volume

        @player.property_observer("time-pos")
        def on_time_pos(_name: str, value: float | None) -> None:
            if value is not None:
                self._state.position = value
                self._notify_state()

        @player.property_observer("duration")
        def on_duration(_name: str, value: float | None) -> None:
            if value is not None:
                self._state.duration = value
                self._notify_state()

        @player.property_observer("pause")
        def on_pause(_name: str, value: bool | None) -> None:
            if value is not None:
                if value:
                    self._state.state = PlayerState.PAUSED
                elif self._state.state == PlayerState.PAUSED:
                    self._state.state = PlayerState.PLAYING
                self._notify_state()

        @player.property_observer("idle-active")
        def on_idle(_name: str, value: bool | None) -> None:
            # Only trigger stop if we're not in the process of starting playback
            # This prevents a race condition where idle-active=True fires during startup
            if value and self._state.state == PlayerState.PLAYING and not self._starting_playback:
                self._state.state = PlayerState.STOPPED
                self._notify_state()
                self._notify_end()

        return player

    @property
    def player(self) -> mpv.MPV:
        """Get or create MPV player."""
        if self._player is None:
            self._player = self._init_player()
        return self._player

    @property
    def state(self) -> PlaybackState:
        """Get current playback state."""
        return self._state

    def on_state_change(self, callback: Callable[[PlaybackState], None]) -> None:
        """Register state change callback."""
        self._state_callbacks.append(callback)

    def on_track_end(self, callback: Callable[[], None]) -> None:
        """Register track end callback."""
        self._end_callbacks.append(callback)

    def _notify_state(self) -> None:
        """Notify state change callbacks."""
        for callback in self._state_callbacks:
            try:
                callback(self._state)
            except Exception as e:
                log.error("State callback error", error=str(e))

    def _notify_end(self) -> None:
        """Notify track end callbacks."""
        for callback in self._end_callbacks:
            try:
                callback()
            except Exception as e:
                log.error("End callback error", error=str(e))

    async def play(self, track: Track) -> None:
        """Play a track."""
        with self._lock:
            # Skip if already playing or loading this track
            if (self._state.current_track and
                self._state.current_track.id == track.id and
                self._state.state in (PlayerState.PLAYING, PlayerState.LOADING)):
                log.debug("Already playing/loading this track, skipping", title=track.title)
                return

            self._state.state = PlayerState.LOADING
            self._state.current_track = track
            self._state.position = 0.0
            self._state.duration = track.duration_seconds
            self._state.error_message = None
            self._notify_state()

            try:
                stream_url = await self._stream_extractor.extract_for_track(track)
                # Set flag to prevent idle-active race condition during startup
                self._starting_playback = True
                self.player.play(stream_url)
                self._state.state = PlayerState.PLAYING
                log.info("Playing track", title=track.title)
            except StreamError as e:
                self._starting_playback = False
                self._state.state = PlayerState.ERROR
                self._state.error_message = str(e)
                log.error("Failed to play track", title=track.title, error=str(e))

            self._notify_state()

        # Wait outside the lock for MPV to start, then clear the flag
        if self._state.state == PlayerState.PLAYING:
            await asyncio.sleep(0.5)
            self._starting_playback = False

    def pause(self) -> None:
        """Pause playback."""
        if self._player:
            self.player.pause = True

    def resume(self) -> None:
        """Resume playback."""
        if self._player:
            self.player.pause = False

    def toggle_pause(self) -> None:
        """Toggle pause state."""
        if self._player:
            self.player.pause = not self.player.pause

    def stop(self) -> None:
        """Stop playback."""
        if self._player:
            self.player.stop()
        self._state.state = PlayerState.STOPPED
        self._state.position = 0.0
        self._notify_state()

    def seek(self, seconds: float, relative: bool = True) -> None:
        """Seek to position."""
        if self._player:
            if relative:
                self.player.seek(seconds, reference="relative")
            else:
                self.player.seek(seconds, reference="absolute")

    def seek_percent(self, percent: float) -> None:
        """Seek to percentage of duration."""
        if self._player and self._state.duration > 0:
            position = (percent / 100) * self._state.duration
            self.seek(position, relative=False)

    def set_volume(self, volume: int) -> None:
        """Set volume (0-100)."""
        volume = max(0, min(100, volume))
        self._state.volume = volume
        if self._player:
            self.player.volume = volume
        self._notify_state()

    def adjust_volume(self, delta: int) -> None:
        """Adjust volume by delta."""
        self.set_volume(self._state.volume + delta)

    def mute(self, muted: bool | None = None) -> None:
        """Set or toggle mute."""
        if muted is None:
            muted = not self._state.muted
        self._state.muted = muted
        if self._player:
            self.player.mute = muted
        self._notify_state()

    def set_repeat(self, mode: RepeatMode) -> None:
        """Set repeat mode."""
        self._state.repeat = mode
        if self._player:
            if mode == RepeatMode.ONE:
                self.player.loop_file = "inf"
            else:
                self.player.loop_file = False
        self._notify_state()

    def cycle_repeat(self) -> RepeatMode:
        """Cycle through repeat modes."""
        modes = [RepeatMode.OFF, RepeatMode.ALL, RepeatMode.ONE]
        current_idx = modes.index(self._state.repeat)
        new_mode = modes[(current_idx + 1) % len(modes)]
        self.set_repeat(new_mode)
        return new_mode

    def close(self) -> None:
        """Clean up resources."""
        if self._player:
            self._player.terminate()
            self._player = None
        self._stream_extractor.close()
