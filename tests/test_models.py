"""Tests for data models."""

import pytest

from squid.api.models import Track, Album, Artist, Playlist, Thumbnail


class TestTrack:
    """Tests for Track model."""

    def test_from_api_basic(self):
        """Test creating track from API response."""
        data = {
            "videoId": "abc123",
            "title": "Test Song",
            "artists": [{"id": "artist1", "name": "Test Artist"}],
            "album": {"id": "album1", "name": "Test Album"},
            "duration": "3:45",
            "thumbnails": [{"url": "http://example.com/thumb.jpg", "width": 120, "height": 120}],
        }
        track = Track.from_api(data)

        assert track.id == "abc123"
        assert track.title == "Test Song"
        assert len(track.artists) == 1
        assert track.artists[0].name == "Test Artist"
        assert track.album.title == "Test Album"
        assert track.duration_seconds == 225
        assert track.duration_str == "3:45"

    def test_duration_str_hours(self):
        """Test duration formatting with hours."""
        track = Track(id="test", title="Test", duration_seconds=3661)
        assert track.duration_str == "1:01:01"

    def test_artist_names(self):
        """Test artist names property."""
        track = Track(
            id="test",
            title="Test",
            artists=[
                Artist(id="1", name="Artist One"),
                Artist(id="2", name="Artist Two"),
            ],
        )
        assert track.artist_names == "Artist One, Artist Two"

    def test_artist_names_empty(self):
        """Test artist names with no artists."""
        track = Track(id="test", title="Test")
        assert track.artist_names == "Unknown Artist"


class TestAlbum:
    """Tests for Album model."""

    def test_from_api(self):
        """Test creating album from API response."""
        data = {
            "browseId": "album123",
            "title": "Test Album",
            "artists": [{"id": "artist1", "name": "Test Artist"}],
            "year": "2024",
            "trackCount": 10,
        }
        album = Album.from_api(data)

        assert album.id == "album123"
        assert album.title == "Test Album"
        assert album.year == "2024"
        assert album.track_count == 10


class TestArtist:
    """Tests for Artist model."""

    def test_from_api(self):
        """Test creating artist from API response."""
        data = {
            "browseId": "artist123",
            "artist": "Test Artist",
            "subscribers": "1.5M",
        }
        artist = Artist.from_api(data)

        assert artist.id == "artist123"
        assert artist.name == "Test Artist"
        assert artist.subscribers == "1.5M"


class TestPlaylist:
    """Tests for Playlist model."""

    def test_from_api(self):
        """Test creating playlist from API response."""
        data = {
            "playlistId": "playlist123",
            "title": "My Playlist",
            "description": "A test playlist",
            "count": 25,
            "author": {"name": "Test User"},
        }
        playlist = Playlist.from_api(data)

        assert playlist.id == "playlist123"
        assert playlist.title == "My Playlist"
        assert playlist.description == "A test playlist"
        assert playlist.track_count == 25
        assert playlist.author == "Test User"
