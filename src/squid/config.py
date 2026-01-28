"""Configuration management for Squid."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir, user_data_dir, user_cache_dir


def get_config_dir() -> Path:
    """Get the configuration directory."""
    path = Path(user_config_dir("squid"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_data_dir() -> Path:
    """Get the data directory."""
    path = Path(user_data_dir("squid"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_cache_dir() -> Path:
    """Get the cache directory."""
    path = Path(user_cache_dir("squid"))
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass
class Config:
    """Application configuration."""

    # Paths
    config_dir: Path = field(default_factory=get_config_dir)
    data_dir: Path = field(default_factory=get_data_dir)
    cache_dir: Path = field(default_factory=get_cache_dir)

    # Playback
    default_volume: int = 80

    # Cache
    cache_ttl_hours: int = 24

    # UI
    theme: str = "default"

    @property
    def oauth_path(self) -> Path:
        """Path to OAuth credentials."""
        return self.config_dir / "oauth.json"

    @property
    def browser_auth_path(self) -> Path:
        """Path to browser authentication headers."""
        return self.config_dir / "browser.json"

    @property
    def db_path(self) -> Path:
        """Path to SQLite cache database."""
        return self.cache_dir / "cache.db"

    @property
    def settings_path(self) -> Path:
        """Path to user settings file."""
        return self.config_dir / "settings.json"

    @property
    def queue_path(self) -> Path:
        """Path to persisted queue."""
        return self.data_dir / "queue.json"

    def save(self) -> None:
        """Save configuration to disk."""
        settings = {
            "default_volume": self.default_volume,
            "cache_ttl_hours": self.cache_ttl_hours,
            "theme": self.theme,
        }
        self.settings_path.write_text(json.dumps(settings, indent=2))

    @classmethod
    def load(cls) -> Config:
        """Load configuration from disk."""
        config = cls()
        if config.settings_path.exists():
            try:
                settings = json.loads(config.settings_path.read_text())
                config.default_volume = settings.get("default_volume", 80)
                config.cache_ttl_hours = settings.get("cache_ttl_hours", 24)
                config.theme = settings.get("theme", "default")
            except (json.JSONDecodeError, KeyError):
                pass
        return config


_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config
