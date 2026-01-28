"""Ex-style command parsing."""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import TYPE_CHECKING


@dataclass
class Command:
    """Parsed command."""

    name: str
    args: list[str]
    raw: str

    @property
    def arg(self) -> str:
        """Get first argument or empty string."""
        return self.args[0] if self.args else ""


class CommandParser:
    """Parser for ex-style commands."""

    # Command aliases
    ALIASES: dict[str, str] = {
        "q": "quit",
        "q!": "quit!",
        "w": "write",
        "e": "edit",
        "set": "set",
        "vol": "volume",
        "v": "volume",
        "seek": "seek",
        "s": "shuffle",
        "r": "repeat",
        "clear": "clear",
        "add": "add",
        "play": "play",
        "pause": "pause",
        "stop": "stop",
        "next": "next",
        "prev": "previous",
        "previous": "previous",
        "search": "search",
        "filter": "filter",
        "sort": "sort",
        "help": "help",
        "h": "help",
        "refresh": "refresh",
        "cache": "cache",
        "auth": "auth",
    }

    def parse(self, input_str: str) -> Command | None:
        """Parse a command string."""
        input_str = input_str.strip()
        if not input_str:
            return None

        try:
            parts = shlex.split(input_str)
        except ValueError:
            parts = input_str.split()

        if not parts:
            return None

        name = parts[0].lower()
        name = self.ALIASES.get(name, name)
        args = parts[1:]

        return Command(name=name, args=args, raw=input_str)

    def get_completions(self, partial: str) -> list[str]:
        """Get command completions for partial input."""
        partial = partial.lower()
        commands = set(self.ALIASES.values())
        return sorted([cmd for cmd in commands if cmd.startswith(partial)])
