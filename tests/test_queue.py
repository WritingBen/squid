"""Tests for play queue."""

import pytest

from squid.api.models import Track
from squid.player.queue import PlayQueue


def make_track(id: str, title: str = "Test") -> Track:
    """Create a test track."""
    return Track(id=id, title=title)


class TestPlayQueue:
    """Tests for PlayQueue."""

    def test_add_track(self):
        """Test adding a track."""
        queue = PlayQueue()
        track = make_track("1", "Track 1")
        queue.add(track)

        assert queue.length == 1
        assert queue.tracks[0] == track

    def test_add_many(self):
        """Test adding multiple tracks."""
        queue = PlayQueue()
        tracks = [make_track(str(i)) for i in range(5)]
        queue.add_many(tracks)

        assert queue.length == 5

    def test_set_current(self):
        """Test setting current track."""
        queue = PlayQueue()
        tracks = [make_track(str(i)) for i in range(3)]
        queue.add_many(tracks)

        queue.set_current(1)
        assert queue.current == tracks[1]
        assert queue.current_index == 1

    def test_next(self):
        """Test advancing to next track."""
        queue = PlayQueue()
        tracks = [make_track(str(i)) for i in range(3)]
        queue.add_many(tracks)
        queue.set_current(0)

        next_track = queue.next()
        assert next_track == tracks[1]
        assert queue.current_index == 1

    def test_next_at_end(self):
        """Test next at end of queue."""
        queue = PlayQueue()
        tracks = [make_track(str(i)) for i in range(3)]
        queue.add_many(tracks)
        queue.set_current(2)

        next_track = queue.next()
        assert next_track is None

    def test_previous(self):
        """Test going to previous track."""
        queue = PlayQueue()
        tracks = [make_track(str(i)) for i in range(3)]
        queue.add_many(tracks)
        queue.set_current(2)

        prev_track = queue.previous()
        assert prev_track == tracks[1]

    def test_remove(self):
        """Test removing a track."""
        queue = PlayQueue()
        tracks = [make_track(str(i)) for i in range(3)]
        queue.add_many(tracks)

        removed = queue.remove(1)
        assert removed == tracks[1]
        assert queue.length == 2

    def test_remove_before_current(self):
        """Test removing track before current adjusts index."""
        queue = PlayQueue()
        tracks = [make_track(str(i)) for i in range(3)]
        queue.add_many(tracks)
        queue.set_current(2)

        queue.remove(0)
        assert queue.current_index == 1

    def test_clear(self):
        """Test clearing the queue."""
        queue = PlayQueue()
        tracks = [make_track(str(i)) for i in range(3)]
        queue.add_many(tracks)

        queue.clear()
        assert queue.is_empty
        assert queue.current_index == -1

    def test_shuffle(self):
        """Test shuffle."""
        queue = PlayQueue()
        tracks = [make_track(str(i)) for i in range(10)]
        queue.add_many(tracks)
        queue.set_current(0)

        queue.shuffle(True)
        assert queue.is_shuffled
        # Current track should still be at index 0
        assert queue.current == tracks[0]
        assert queue.current_index == 0

    def test_unshuffle(self):
        """Test disabling shuffle restores order."""
        queue = PlayQueue()
        tracks = [make_track(str(i)) for i in range(10)]
        queue.add_many(tracks)
        queue.set_current(0)

        queue.shuffle(True)
        queue.shuffle(False)
        assert not queue.is_shuffled
        # Should be back to original order
        assert queue.tracks == tracks

    def test_move(self):
        """Test moving a track."""
        queue = PlayQueue()
        tracks = [make_track(str(i)) for i in range(5)]
        queue.add_many(tracks)

        queue.move(0, 2)
        assert queue.tracks[0] == tracks[1]
        assert queue.tracks[2] == tracks[0]

    def test_add_next(self):
        """Test adding track to play next."""
        queue = PlayQueue()
        tracks = [make_track(str(i)) for i in range(3)]
        queue.add_many(tracks)
        queue.set_current(0)

        new_track = make_track("new")
        queue.add_next(new_track)

        assert queue.tracks[1] == new_track

    def test_replace(self):
        """Test replacing queue contents."""
        queue = PlayQueue()
        old_tracks = [make_track(str(i)) for i in range(3)]
        queue.add_many(old_tracks)

        new_tracks = [make_track(str(i + 10)) for i in range(5)]
        queue.replace(new_tracks, start_index=2)

        assert queue.length == 5
        assert queue.current_index == 2
        assert queue.tracks == new_tracks
