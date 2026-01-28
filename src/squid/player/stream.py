"""Stream URL extraction using yt-dlp."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import TYPE_CHECKING

import structlog
import yt_dlp

if TYPE_CHECKING:
    from squid.api.models import Track

log = structlog.get_logger()


class StreamError(Exception):
    """Stream extraction error."""

    pass


class StreamExtractor:
    """Extract audio stream URLs using yt-dlp."""

    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._ydl_opts = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }

    def _extract_sync(self, video_id: str) -> str:
        """Synchronously extract stream URL."""
        url = f"https://music.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL(self._ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise StreamError(f"Failed to extract info for {video_id}")

            # Get best audio URL
            if "url" in info:
                return info["url"]

            formats = info.get("formats", [])
            audio_formats = [f for f in formats if f.get("acodec") != "none"]
            if not audio_formats:
                audio_formats = formats

            if not audio_formats:
                raise StreamError(f"No audio formats found for {video_id}")

            # Prefer higher quality
            best = max(audio_formats, key=lambda f: f.get("abr", 0) or 0)
            return best["url"]

    async def extract(self, video_id: str) -> str:
        """Extract stream URL for a video ID."""
        log.info("Extracting stream URL", video_id=video_id)
        loop = asyncio.get_event_loop()
        try:
            url = await loop.run_in_executor(
                self._executor, partial(self._extract_sync, video_id)
            )
            log.debug("Stream URL extracted", video_id=video_id)
            return url
        except Exception as e:
            log.error("Stream extraction failed", video_id=video_id, error=str(e))
            raise StreamError(f"Failed to extract stream: {e}") from e

    async def extract_for_track(self, track: Track) -> str:
        """Extract stream URL for a track."""
        video_id = track.video_id or track.id
        if not video_id:
            raise StreamError("Track has no video ID")
        return await self.extract(video_id)

    def close(self) -> None:
        """Clean up resources."""
        self._executor.shutdown(wait=False)
