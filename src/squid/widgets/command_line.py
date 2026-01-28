"""Vim-style command line input widget."""

from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, Label
from textual.containers import Horizontal


class CommandLine(Widget):
    """Vim-style command line input (: and / modes)."""

    DEFAULT_CSS = """
    CommandLine {
        width: 100%;
        height: 1;
        background: $surface;
        display: none;
    }

    CommandLine.active {
        display: block;
    }

    CommandLine Horizontal {
        width: 100%;
    }

    CommandLine .command-prefix {
        width: 1;
        color: ansi_yellow;
    }

    CommandLine Input {
        width: 1fr;
        border: none;
        background: transparent;
        padding: 0;
    }

    CommandLine Input:focus {
        border: none;
    }
    """

    class CommandSubmitted(Message):
        """Command was submitted."""

        def __init__(self, command: str, mode: str) -> None:
            super().__init__()
            self.command = command
            self.mode = mode  # "command" or "search"

    class CommandCancelled(Message):
        """Command input was cancelled."""

        pass

    is_active: reactive[bool] = reactive(False)
    mode: reactive[str] = reactive("command")  # "command" or "search"

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(":", id="prefix", classes="command-prefix")
            yield Input(id="input")

    def watch_is_active(self, active: bool) -> None:
        """Show/hide command line."""
        if active:
            self.add_class("active")
            self.query_one("#input", Input).focus()
        else:
            self.remove_class("active")
            self.query_one("#input", Input).value = ""

    def watch_mode(self, mode: str) -> None:
        """Update prefix based on mode."""
        prefix = self.query_one("#prefix", Label)
        prefix.update(":" if mode == "command" else "/")

    def activate(self, mode: str = "command") -> None:
        """Activate command line."""
        self.mode = mode
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate command line."""
        self.is_active = False

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission."""
        command = event.value.strip()
        if command:
            self.post_message(self.CommandSubmitted(command, self.mode))
        self.deactivate()

    def on_key(self, event: events.Key) -> None:
        """Handle escape key."""
        if event.key == "escape":
            self.deactivate()
            self.post_message(self.CommandCancelled())
            event.stop()
