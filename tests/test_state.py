"""Tests for playback state."""

import pytest

from squid.player.state import PlaybackState, PlayerState, RepeatMode


class TestPlaybackState:
    """Tests for PlaybackState."""

    def test_default_state(self):
        """Test default state values."""
        state = PlaybackState()

        assert state.state == PlayerState.STOPPED
        assert state.current_track is None
        assert state.position == 0.0
        assert state.duration == 0.0
        assert state.volume == 80
        assert not state.muted
        assert not state.shuffle
        assert state.repeat == RepeatMode.OFF

    def test_position_str(self):
        """Test position formatting."""
        state = PlaybackState(position=125.5)
        assert state.position_str == "2:05"

    def test_position_str_hours(self):
        """Test position formatting with hours."""
        state = PlaybackState(position=3725.0)
        assert state.position_str == "1:02:05"

    def test_progress_percent(self):
        """Test progress percentage calculation."""
        state = PlaybackState(position=30.0, duration=120.0)
        assert state.progress_percent == 25.0

    def test_progress_percent_zero_duration(self):
        """Test progress with zero duration."""
        state = PlaybackState(position=30.0, duration=0.0)
        assert state.progress_percent == 0.0

    def test_is_playing(self):
        """Test is_playing property."""
        state = PlaybackState(state=PlayerState.PLAYING)
        assert state.is_playing
        assert not state.is_paused
        assert not state.is_stopped

    def test_is_paused(self):
        """Test is_paused property."""
        state = PlaybackState(state=PlayerState.PAUSED)
        assert state.is_paused
        assert not state.is_playing

    def test_copy(self):
        """Test copying state with modifications."""
        state = PlaybackState(volume=50, shuffle=True)
        new_state = state.copy(volume=75, muted=True)

        assert new_state.volume == 75
        assert new_state.muted
        assert new_state.shuffle  # Preserved from original
        assert state.volume == 50  # Original unchanged
