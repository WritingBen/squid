"""SQLite caching for API responses."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, TYPE_CHECKING
from contextlib import asynccontextmanager

import aiosqlite
import structlog

if TYPE_CHECKING:
    from squid.config import Config

log = structlog.get_logger()

SCHEMA = """
CREATE TABLE IF NOT EXISTS cache (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at);
"""


class Cache:
    """Async SQLite cache for API responses."""

    def __init__(self, db_path: Path, ttl_hours: int = 24) -> None:
        self.db_path = db_path
        self.ttl = timedelta(hours=ttl_hours)
        self._db: aiosqlite.Connection | None = None
        self._lock = threading.Lock()  # Use threading lock for cross-event-loop safety

    @asynccontextmanager
    async def _async_lock(self):
        """Async context manager wrapper for threading lock.

        Uses run_in_executor to avoid blocking the event loop during acquire.
        """
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._lock.acquire)
        try:
            yield
        finally:
            self._lock.release()

    async def _get_db(self) -> aiosqlite.Connection:
        """Get or create database connection."""
        if self._db is None:
            self._db = await aiosqlite.connect(self.db_path)
            await self._db.executescript(SCHEMA)
            await self._db.commit()
        return self._db

    async def get(self, key: str) -> Any | None:
        """Get cached value if not expired."""
        async with self._async_lock():
            db = await self._get_db()
            cursor = await db.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
            )
            row = await cursor.fetchone()
            if row is None:
                return None

            value, expires_at = row
            if datetime.fromisoformat(expires_at) < datetime.now():
                await db.execute("DELETE FROM cache WHERE key = ?", (key,))
                await db.commit()
                return None

            return json.loads(value)

    async def set(self, key: str, value: Any, ttl: timedelta | None = None) -> None:
        """Set cached value with expiration."""
        async with self._async_lock():
            db = await self._get_db()
            expires_at = datetime.now() + (ttl or self.ttl)
            await db.execute(
                """
                INSERT OR REPLACE INTO cache (key, value, expires_at)
                VALUES (?, ?, ?)
                """,
                (key, json.dumps(value), expires_at.isoformat()),
            )
            await db.commit()

    async def delete(self, key: str) -> None:
        """Delete cached value."""
        async with self._async_lock():
            db = await self._get_db()
            await db.execute("DELETE FROM cache WHERE key = ?", (key,))
            await db.commit()

    async def clear(self) -> None:
        """Clear all cached values."""
        async with self._async_lock():
            db = await self._get_db()
            await db.execute("DELETE FROM cache")
            await db.commit()

    async def cleanup_expired(self) -> int:
        """Remove expired entries, returns count of removed."""
        async with self._async_lock():
            db = await self._get_db()
            cursor = await db.execute(
                "DELETE FROM cache WHERE expires_at < ?",
                (datetime.now().isoformat(),),
            )
            await db.commit()
            return cursor.rowcount

    async def close(self) -> None:
        """Close database connection."""
        if self._db:
            await self._db.close()
            self._db = None
