"""Tests for keybindings."""

import pytest

from squid.keybindings.bindings import Keybindings, Action, DEFAULT_BINDINGS
from squid.keybindings.command_parser import CommandParser


class TestKeybindings:
    """Tests for Keybindings."""

    def test_default_bindings(self):
        """Test default bindings are set."""
        kb = Keybindings()

        assert kb.get_action("j") == Action.CURSOR_DOWN
        assert kb.get_action("k") == Action.CURSOR_UP
        assert kb.get_action("c") == Action.PLAY_PAUSE
        assert kb.get_action("1") == Action.VIEW_LIBRARY_TREE

    def test_get_action_unknown(self):
        """Test getting unknown key returns None."""
        kb = Keybindings()
        assert kb.get_action("unknown_key") is None

    def test_set_binding(self):
        """Test setting a new binding."""
        kb = Keybindings()
        kb.set_binding("x", Action.QUIT)

        assert kb.get_action("x") == Action.QUIT

    def test_remove_binding(self):
        """Test removing a binding."""
        kb = Keybindings()
        kb.remove_binding("j")

        assert kb.get_action("j") is None

    def test_get_keys_for_action(self):
        """Test getting all keys for an action."""
        kb = Keybindings()
        keys = kb.get_keys_for_action(Action.VOLUME_UP)

        assert "+" in keys
        assert "=" in keys

    def test_serialization(self):
        """Test serialization round-trip."""
        kb = Keybindings()
        data = kb.to_dict()
        restored = Keybindings.from_dict(data)

        assert restored.get_action("j") == kb.get_action("j")
        assert restored.get_action("c") == kb.get_action("c")


class TestCommandParser:
    """Tests for CommandParser."""

    def test_parse_simple(self):
        """Test parsing simple command."""
        parser = CommandParser()
        cmd = parser.parse("quit")

        assert cmd.name == "quit"
        assert cmd.args == []

    def test_parse_with_args(self):
        """Test parsing command with arguments."""
        parser = CommandParser()
        cmd = parser.parse("volume 75")

        assert cmd.name == "volume"
        assert cmd.args == ["75"]
        assert cmd.arg == "75"

    def test_parse_alias(self):
        """Test alias resolution."""
        parser = CommandParser()
        cmd = parser.parse("q")

        assert cmd.name == "quit"

    def test_parse_empty(self):
        """Test parsing empty string."""
        parser = CommandParser()
        cmd = parser.parse("")

        assert cmd is None

    def test_parse_quoted_args(self):
        """Test parsing quoted arguments."""
        parser = CommandParser()
        cmd = parser.parse('search "hello world"')

        assert cmd.name == "search"
        assert cmd.args == ["hello world"]

    def test_completions(self):
        """Test command completions."""
        parser = CommandParser()
        completions = parser.get_completions("qu")

        assert "quit" in completions

    def test_completions_empty(self):
        """Test completions for non-matching prefix."""
        parser = CommandParser()
        completions = parser.get_completions("xyz")

        assert completions == []
