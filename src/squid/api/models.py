"""Data models for YouTube Music entities."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Thumbnail(BaseModel):
    """Thumbnail image."""

    url: str
    width: int = 0
    height: int = 0


class Artist(BaseModel):
    """Artist model."""

    id: str
    name: str
    thumbnails: list[Thumbnail] = Field(default_factory=list)
    subscribers: str | None = None
    albums: list[Album] = Field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict) -> Artist:
        """Create from API response."""
        thumbnails = [
            Thumbnail(url=t.get("url", ""), width=t.get("width", 0), height=t.get("height", 0))
            for t in data.get("thumbnails", [])
        ]
        # Handle None IDs - use empty string as fallback
        artist_id = data.get("browseId") or data.get("id") or ""
        return cls(
            id=artist_id,
            name=data.get("artist", data.get("name", "Unknown Artist")),
            thumbnails=thumbnails,
            subscribers=data.get("subscribers"),
        )


class Album(BaseModel):
    """Album model."""

    id: str
    title: str
    artists: list[Artist] = Field(default_factory=list)
    thumbnails: list[Thumbnail] = Field(default_factory=list)
    year: str | None = None
    track_count: int | None = None
    tracks: list[Track] = Field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict) -> Album:
        """Create from API response."""
        thumbnails = [
            Thumbnail(url=t.get("url", ""), width=t.get("width", 0), height=t.get("height", 0))
            for t in data.get("thumbnails", [])
        ]
        artists = []
        for a in data.get("artists", []):
            if isinstance(a, dict):
                artist_id = a.get("id") or ""
                artists.append(
                    Artist(id=artist_id, name=a.get("name", "Unknown Artist"))
                )
        # Handle None IDs
        album_id = data.get("browseId") or data.get("playlistId") or data.get("id") or ""
        return cls(
            id=album_id,
            title=data.get("title", "Unknown Album"),
            artists=artists,
            thumbnails=thumbnails,
            year=data.get("year"),
            track_count=data.get("trackCount"),
        )


class Track(BaseModel):
    """Track model."""

    id: str
    title: str
    artists: list[Artist] = Field(default_factory=list)
    album: Album | None = None
    duration_seconds: int = 0
    thumbnails: list[Thumbnail] = Field(default_factory=list)
    is_explicit: bool = False
    is_available: bool = True
    video_id: str | None = None
    set_video_id: str | None = None  # For playlist track removal

    @property
    def duration_str(self) -> str:
        """Format duration as MM:SS or HH:MM:SS."""
        minutes, seconds = divmod(self.duration_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    @property
    def artist_names(self) -> str:
        """Get comma-separated artist names."""
        return ", ".join(a.name for a in self.artists) or "Unknown Artist"

    @classmethod
    def from_api(cls, data: dict) -> Track:
        """Create from API response."""
        thumbnails = [
            Thumbnail(url=t.get("url", ""), width=t.get("width", 0), height=t.get("height", 0))
            for t in data.get("thumbnails", [])
        ]
        artists = []
        for a in data.get("artists", []):
            if isinstance(a, dict):
                artist_id = a.get("id") or ""
                artists.append(
                    Artist(id=artist_id, name=a.get("name", "Unknown Artist"))
                )

        album_data = data.get("album")
        album = None
        if album_data and isinstance(album_data, dict):
            album_id = album_data.get("id") or ""
            album = Album(
                id=album_id,
                title=album_data.get("name", "Unknown Album"),
            )

        duration = data.get("duration_seconds", 0)
        if not duration and data.get("duration"):
            parts = str(data["duration"]).split(":")
            if len(parts) == 2:
                duration = int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

        # Handle None IDs
        track_id = data.get("videoId") or data.get("id") or ""

        return cls(
            id=track_id,
            title=data.get("title", "Unknown Track"),
            artists=artists,
            album=album,
            duration_seconds=duration,
            thumbnails=thumbnails,
            is_explicit=data.get("isExplicit", False),
            is_available=data.get("isAvailable", True),
            video_id=data.get("videoId"),
            set_video_id=data.get("setVideoId"),
        )


class Playlist(BaseModel):
    """Playlist model."""

    id: str
    title: str
    description: str = ""
    thumbnails: list[Thumbnail] = Field(default_factory=list)
    track_count: int = 0
    tracks: list[Track] = Field(default_factory=list)
    author: str | None = None
    privacy: Literal["PUBLIC", "PRIVATE", "UNLISTED"] = "PRIVATE"

    @classmethod
    def from_api(cls, data: dict) -> Playlist:
        """Create from API response."""
        thumbnails = [
            Thumbnail(url=t.get("url", ""), width=t.get("width", 0), height=t.get("height", 0))
            for t in data.get("thumbnails", [])
        ]

        # Handle author which can be a string, dict, or list of dicts
        author_data = data.get("author")
        author = None
        if isinstance(author_data, str):
            author = author_data
        elif isinstance(author_data, dict):
            author = author_data.get("name")
        elif isinstance(author_data, list) and author_data:
            # List of author dicts - take the first one
            first_author = author_data[0]
            if isinstance(first_author, dict):
                author = first_author.get("name")

        # Handle None IDs
        playlist_id = data.get("playlistId") or data.get("id") or ""

        return cls(
            id=playlist_id,
            title=data.get("title", "Unknown Playlist"),
            description=data.get("description") or "",
            thumbnails=thumbnails,
            track_count=data.get("count", data.get("trackCount", 0)) or 0,
            author=author,
            privacy=data.get("privacy", "PRIVATE"),
        )


class SearchResults(BaseModel):
    """Search results container."""

    tracks: list[Track] = Field(default_factory=list)
    albums: list[Album] = Field(default_factory=list)
    artists: list[Artist] = Field(default_factory=list)
    playlists: list[Playlist] = Field(default_factory=list)


class LibraryData(BaseModel):
    """User's library data."""

    artists: list[Artist] = Field(default_factory=list)
    albums: list[Album] = Field(default_factory=list)
    playlists: list[Playlist] = Field(default_factory=list)
    liked_songs: Playlist | None = None
    last_updated: datetime = Field(default_factory=datetime.now)
