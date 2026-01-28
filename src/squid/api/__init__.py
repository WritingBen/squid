"""YouTube Music API layer."""

from squid.api.models import Track, Album, Artist, Playlist
from squid.api.client import YouTubeMusicClient
from squid.api.auth import AuthManager

__all__ = [
    "Track",
    "Album",
    "Artist",
    "Playlist",
    "YouTubeMusicClient",
    "AuthManager",
]
