"""Async wrapper for ytmusicapi."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import TYPE_CHECKING, Any

import structlog
from ytmusicapi import YTMusic

from squid.api.auth import AuthManager
from squid.api.cache import Cache
from squid.api.models import (
    Album,
    Artist,
    LibraryData,
    Playlist,
    SearchResults,
    Track,
)

if TYPE_CHECKING:
    from squid.config import Config

log = structlog.get_logger()


class YouTubeMusicClient:
    """Async wrapper around ytmusicapi with caching."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.auth = AuthManager(config)
        self.cache = Cache(config.db_path, config.cache_ttl_hours)
        self._ytmusic: YTMusic | None = None
        self._executor = ThreadPoolExecutor(max_workers=4)

    @property
    def ytmusic(self) -> YTMusic:
        """Get authenticated YTMusic instance."""
        if self._ytmusic is None:
            self._ytmusic = self.auth.get_ytmusic()
        return self._ytmusic

    async def _run_sync(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Run synchronous function in thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, partial(func, *args, **kwargs)
        )

    async def get_library_artists(self, limit: int = 100) -> list[Artist]:
        """Get user's library artists."""
        cache_key = f"library_artists_{limit}"
        cached = await self.cache.get(cache_key)
        if cached:
            return [Artist.model_validate(a) for a in cached]

        log.info("Fetching library artists")
        data = await self._run_sync(self.ytmusic.get_library_artists, limit=limit)
        artists = [Artist.from_api(a) for a in (data or [])]

        await self.cache.set(cache_key, [a.model_dump() for a in artists])
        return artists

    async def get_library_albums(self, limit: int = 100) -> list[Album]:
        """Get user's library albums."""
        cache_key = f"library_albums_{limit}"
        cached = await self.cache.get(cache_key)
        if cached:
            return [Album.model_validate(a) for a in cached]

        log.info("Fetching library albums")
        data = await self._run_sync(self.ytmusic.get_library_albums, limit=limit)
        albums = [Album.from_api(a) for a in (data or [])]

        await self.cache.set(cache_key, [a.model_dump() for a in albums])
        return albums

    async def get_library_playlists(self, limit: int = 100) -> list[Playlist]:
        """Get user's playlists."""
        cache_key = f"library_playlists_{limit}"
        cached = await self.cache.get(cache_key)
        if cached:
            return [Playlist.model_validate(p) for p in cached]

        log.info("Fetching library playlists")
        data = await self._run_sync(self.ytmusic.get_library_playlists, limit=limit)
        playlists = [Playlist.from_api(p) for p in (data or [])]

        await self.cache.set(cache_key, [p.model_dump() for p in playlists])
        return playlists

    async def get_liked_songs(self, limit: int = 1000) -> Playlist:
        """Get user's liked songs playlist."""
        cache_key = f"liked_songs_{limit}"
        cached = await self.cache.get(cache_key)
        if cached:
            return Playlist.model_validate(cached)

        log.info("Fetching liked songs")
        data = await self._run_sync(self.ytmusic.get_liked_songs, limit=limit)
        playlist = Playlist(
            id="LM",
            title="Liked Songs",
            tracks=[Track.from_api(t) for t in (data.get("tracks", []) if data else [])],
            track_count=len(data.get("tracks", [])) if data else 0,
        )

        await self.cache.set(cache_key, playlist.model_dump())
        return playlist

    async def get_artist(self, artist_id: str) -> Artist:
        """Get artist details with albums."""
        cache_key = f"artist_{artist_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return Artist.model_validate(cached)

        log.info("Fetching artist", artist_id=artist_id)
        data = await self._run_sync(self.ytmusic.get_artist, artist_id)
        artist = Artist.from_api(data)

        albums_data = data.get("albums", {}).get("results", [])
        artist.albums = [Album.from_api(a) for a in albums_data]

        await self.cache.set(cache_key, artist.model_dump())
        return artist

    async def get_album(self, album_id: str) -> Album:
        """Get album details with tracks."""
        cache_key = f"album_{album_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return Album.model_validate(cached)

        log.info("Fetching album", album_id=album_id)
        data = await self._run_sync(self.ytmusic.get_album, album_id)
        album = Album.from_api(data)
        album.tracks = [Track.from_api(t) for t in data.get("tracks", [])]

        await self.cache.set(cache_key, album.model_dump())
        return album

    async def get_playlist(self, playlist_id: str, limit: int = 1000) -> Playlist:
        """Get playlist details with tracks."""
        cache_key = f"playlist_{playlist_id}_{limit}"
        cached = await self.cache.get(cache_key)
        if cached:
            return Playlist.model_validate(cached)

        log.info("Fetching playlist", playlist_id=playlist_id)
        data = await self._run_sync(self.ytmusic.get_playlist, playlist_id, limit=limit)
        playlist = Playlist.from_api(data)
        playlist.tracks = [Track.from_api(t) for t in data.get("tracks", [])]

        await self.cache.set(cache_key, playlist.model_dump())
        return playlist

    async def search(
        self,
        query: str,
        filter_type: str | None = None,
        limit: int = 20,
    ) -> SearchResults:
        """Search YouTube Music."""
        log.info("Searching", query=query, filter=filter_type)
        data = await self._run_sync(
            self.ytmusic.search, query, filter=filter_type, limit=limit
        )

        results = SearchResults()
        for item in data or []:
            result_type = item.get("resultType", "")
            if result_type == "song":
                results.tracks.append(Track.from_api(item))
            elif result_type == "album":
                results.albums.append(Album.from_api(item))
            elif result_type == "artist":
                results.artists.append(Artist.from_api(item))
            elif result_type == "playlist":
                results.playlists.append(Playlist.from_api(item))

        return results

    async def get_library_data(self) -> LibraryData:
        """Get complete library data."""
        artists, albums, playlists, liked = await asyncio.gather(
            self.get_library_artists(),
            self.get_library_albums(),
            self.get_library_playlists(),
            self.get_liked_songs(),
        )
        return LibraryData(
            artists=artists,
            albums=albums,
            playlists=playlists,
            liked_songs=liked,
        )

    async def clear_cache(self) -> None:
        """Clear all cached data."""
        await self.cache.clear()
        log.info("Cache cleared")

    async def close(self) -> None:
        """Clean up resources."""
        await self.cache.close()
        self._executor.shutdown(wait=False)
