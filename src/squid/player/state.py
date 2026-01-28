"""Playback state management."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from squid.api.models import Track


class PlayerState(Enum):
    """Player state enum."""

    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()
    LOADING = auto()
    ERROR = auto()


class RepeatMode(Enum):
    """Repeat mode enum."""

    OFF = auto()
    ALL = auto()
    ONE = auto()


@dataclass
class PlaybackState:
    """Current playback state."""

    state: PlayerState = PlayerState.STOPPED
    current_track: Track | None = None
    position: float = 0.0
    duration: float = 0.0
    volume: int = 80
    muted: bool = False
    shuffle: bool = False
    repeat: RepeatMode = RepeatMode.OFF
    error_message: str | None = None

    @property
    def position_str(self) -> str:
        """Format position as MM:SS."""
        minutes, seconds = divmod(int(self.position), 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    @property
    def duration_str(self) -> str:
        """Format duration as MM:SS."""
        minutes, seconds = divmod(int(self.duration), 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    @property
    def progress_percent(self) -> float:
        """Get playback progress as percentage (0-100)."""
        if self.duration <= 0:
            return 0.0
        return min(100.0, (self.position / self.duration) * 100)

    @property
    def is_playing(self) -> bool:
        """Check if actively playing."""
        return self.state == PlayerState.PLAYING

    @property
    def is_paused(self) -> bool:
        """Check if paused."""
        return self.state == PlayerState.PAUSED

    @property
    def is_stopped(self) -> bool:
        """Check if stopped."""
        return self.state == PlayerState.STOPPED

    def copy(self, **kwargs) -> PlaybackState:
        """Create a copy with updated fields."""
        return PlaybackState(
            state=kwargs.get("state", self.state),
            current_track=kwargs.get("current_track", self.current_track),
            position=kwargs.get("position", self.position),
            duration=kwargs.get("duration", self.duration),
            volume=kwargs.get("volume", self.volume),
            muted=kwargs.get("muted", self.muted),
            shuffle=kwargs.get("shuffle", self.shuffle),
            repeat=kwargs.get("repeat", self.repeat),
            error_message=kwargs.get("error_message", self.error_message),
        )
