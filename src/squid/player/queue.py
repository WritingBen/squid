"""Play queue management."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from squid.api.models import Track

log = structlog.get_logger()


@dataclass
class PlayQueue:
    """Manages the play queue with shuffle support."""

    _tracks: list[Track] = field(default_factory=list)
    _original_order: list[Track] = field(default_factory=list)
    _current_index: int = -1
    _shuffled: bool = False
    _history: list[Track] = field(default_factory=list)

    @property
    def tracks(self) -> list[Track]:
        """Get current queue."""
        return self._tracks

    @property
    def current(self) -> Track | None:
        """Get current track."""
        if 0 <= self._current_index < len(self._tracks):
            return self._tracks[self._current_index]
        return None

    @property
    def current_index(self) -> int:
        """Get current track index."""
        return self._current_index

    @property
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._tracks) == 0

    @property
    def length(self) -> int:
        """Get queue length."""
        return len(self._tracks)

    @property
    def is_shuffled(self) -> bool:
        """Check if shuffle is active."""
        return self._shuffled

    def add(self, track: Track) -> None:
        """Add track to end of queue."""
        self._tracks.append(track)
        self._original_order.append(track)
        log.debug("Track added to queue", title=track.title)

    def add_next(self, track: Track) -> None:
        """Add track to play next."""
        insert_pos = self._current_index + 1
        self._tracks.insert(insert_pos, track)
        self._original_order.insert(insert_pos, track)
        log.debug("Track added to play next", title=track.title)

    def add_many(self, tracks: list[Track]) -> None:
        """Add multiple tracks to queue."""
        self._tracks.extend(tracks)
        self._original_order.extend(tracks)
        log.debug("Added tracks to queue", count=len(tracks))

    def remove(self, index: int) -> Track | None:
        """Remove track at index."""
        if 0 <= index < len(self._tracks):
            track = self._tracks.pop(index)
            if track in self._original_order:
                self._original_order.remove(track)
            if index < self._current_index:
                self._current_index -= 1
            elif index == self._current_index:
                self._current_index = min(self._current_index, len(self._tracks) - 1)
            log.debug("Track removed from queue", title=track.title)
            return track
        return None

    def clear(self) -> None:
        """Clear the queue."""
        self._tracks.clear()
        self._original_order.clear()
        self._current_index = -1
        self._history.clear()
        log.debug("Queue cleared")

    def set_current(self, index: int) -> Track | None:
        """Set current track by index."""
        if 0 <= index < len(self._tracks):
            self._current_index = index
            return self._tracks[index]
        return None

    def next(self) -> Track | None:
        """Advance to next track."""
        if self.current:
            self._history.append(self.current)

        if self._current_index < len(self._tracks) - 1:
            self._current_index += 1
            return self.current
        return None

    def previous(self) -> Track | None:
        """Go to previous track."""
        if self._history:
            # Go back in history
            prev = self._history.pop()
            # Find it in queue
            try:
                idx = self._tracks.index(prev)
                self._current_index = idx
                return prev
            except ValueError:
                pass

        if self._current_index > 0:
            self._current_index -= 1
            return self.current
        return None

    def shuffle(self, enabled: bool) -> None:
        """Enable or disable shuffle."""
        if enabled and not self._shuffled:
            # Save current track
            current = self.current
            # Shuffle
            random.shuffle(self._tracks)
            # Move current to front
            if current and current in self._tracks:
                self._tracks.remove(current)
                self._tracks.insert(0, current)
                self._current_index = 0
            self._shuffled = True
            log.debug("Shuffle enabled")
        elif not enabled and self._shuffled:
            # Restore original order
            current = self.current
            self._tracks = self._original_order.copy()
            if current and current in self._tracks:
                self._current_index = self._tracks.index(current)
            self._shuffled = False
            log.debug("Shuffle disabled")

    def move(self, from_index: int, to_index: int) -> bool:
        """Move track from one position to another."""
        if not (0 <= from_index < len(self._tracks) and 0 <= to_index < len(self._tracks)):
            return False

        track = self._tracks.pop(from_index)
        self._tracks.insert(to_index, track)

        # Update current index
        if from_index == self._current_index:
            self._current_index = to_index
        elif from_index < self._current_index <= to_index:
            self._current_index -= 1
        elif to_index <= self._current_index < from_index:
            self._current_index += 1

        return True

    def replace(self, tracks: list[Track], start_index: int = 0) -> None:
        """Replace queue contents and set starting position."""
        self.clear()
        self._tracks = tracks.copy()
        self._original_order = tracks.copy()
        self._current_index = start_index if tracks else -1

    def to_dict(self) -> dict:
        """Serialize queue to dict."""
        return {
            "tracks": [t.model_dump() for t in self._tracks],
            "current_index": self._current_index,
            "shuffled": self._shuffled,
        }

    @classmethod
    def from_dict(cls, data: dict, track_class) -> PlayQueue:
        """Deserialize queue from dict."""
        queue = cls()
        tracks = [track_class.model_validate(t) for t in data.get("tracks", [])]
        queue._tracks = tracks
        queue._original_order = tracks.copy()
        queue._current_index = data.get("current_index", -1)
        queue._shuffled = data.get("shuffled", False)
        return queue

    def save(self, path: Path) -> None:
        """Save queue to file."""
        path.write_text(json.dumps(self.to_dict(), indent=2))
        log.debug("Queue saved", path=str(path))

    @classmethod
    def load(cls, path: Path, track_class) -> PlayQueue:
        """Load queue from file."""
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text())
            return cls.from_dict(data, track_class)
        except (json.JSONDecodeError, KeyError) as e:
            log.warning("Failed to load queue", error=str(e))
            return cls()
