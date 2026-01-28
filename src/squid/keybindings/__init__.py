"""Keybinding handling."""

from squid.keybindings.bindings import Keybindings, DEFAULT_BINDINGS
from squid.keybindings.command_parser import CommandParser, Command

__all__ = [
    "Keybindings",
    "DEFAULT_BINDINGS",
    "CommandParser",
    "Command",
]
