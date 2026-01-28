"""Settings view (View 7)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static, DataTable, Button, Label
from textual.binding import Binding

if TYPE_CHECKING:
    from squid.keybindings.bindings import Keybindings, Action


class SettingsView(Widget):
    """View 7: Settings and keybindings."""

    BINDINGS = [
        Binding("6", "noop", "[Settings]", key_display=" ", show=True),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    DEFAULT_CSS = """
    SettingsView {
        layout: vertical;
        width: 100%;
        height: 100%;
    }

    SettingsView .pane-header {
        height: 1;
        background: ansi_blue;
        color: ansi_white;
        padding: 0 1;
    }

    SettingsView .settings-section {
        padding: 1;
        margin: 1;
        border: round ansi_blue;
    }

    SettingsView .section-title {
        text-style: bold;
        padding: 0 0 1 0;
    }

    SettingsView .setting-row {
        height: 1;
        padding: 0 1;
    }

    SettingsView .setting-label {
        width: 30;
    }

    SettingsView .setting-value {
        width: 1fr;
        color: ansi_cyan;
    }

    SettingsView .keybindings-table {
        height: auto;
        max-height: 20;
    }

    SettingsView .actions-row {
        height: 3;
        padding: 1;
    }

    SettingsView Button {
        margin: 0 1;
    }
    """

    class CacheCleared(Message):
        """Cache was cleared."""

        pass

    class AuthRefresh(Message):
        """Auth refresh requested."""

        pass

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._keybindings: Keybindings | None = None

    def compose(self) -> ComposeResult:
        yield Static("Settings", classes="pane-header")
        with VerticalScroll():
            # General settings
            with Vertical(classes="settings-section"):
                yield Static("General", classes="section-title")
                with Horizontal(classes="setting-row"):
                    yield Label("Config directory:", classes="setting-label")
                    yield Label("~/.config/squid", id="config-dir", classes="setting-value")
                with Horizontal(classes="setting-row"):
                    yield Label("Cache directory:", classes="setting-label")
                    yield Label("~/.cache/squid", id="cache-dir", classes="setting-value")
                with Horizontal(classes="setting-row"):
                    yield Label("Authentication:", classes="setting-label")
                    yield Label("Not authenticated", id="auth-status", classes="setting-value")

            # Playback settings
            with Vertical(classes="settings-section"):
                yield Static("Playback", classes="section-title")
                with Horizontal(classes="setting-row"):
                    yield Label("Default volume:", classes="setting-label")
                    yield Label("80%", id="default-volume", classes="setting-value")
                with Horizontal(classes="setting-row"):
                    yield Label("Cache TTL:", classes="setting-label")
                    yield Label("24 hours", id="cache-ttl", classes="setting-value")

            # Keybindings
            with Vertical(classes="settings-section"):
                yield Static("Keybindings", classes="section-title")
                table = DataTable(id="keybindings-table", cursor_type="row", classes="keybindings-table")
                table.add_columns("Key", "Action")
                yield table

            # Actions
            with Horizontal(classes="actions-row"):
                yield Button("Clear Cache", id="clear-cache", variant="warning")
                yield Button("Re-authenticate", id="reauth", variant="primary")

    def update_settings(
        self,
        config_dir: str,
        cache_dir: str,
        is_authenticated: bool,
        default_volume: int,
        cache_ttl: int,
        keybindings: Keybindings,
    ) -> None:
        """Update settings display."""
        self.query_one("#config-dir", Label).update(config_dir)
        self.query_one("#cache-dir", Label).update(cache_dir)
        self.query_one("#auth-status", Label).update(
            "Authenticated" if is_authenticated else "Not authenticated"
        )
        self.query_one("#default-volume", Label).update(f"{default_volume}%")
        self.query_one("#cache-ttl", Label).update(f"{cache_ttl} hours")

        self._keybindings = keybindings
        self._refresh_keybindings()

    def _refresh_keybindings(self) -> None:
        """Refresh keybindings table."""
        if not self._keybindings:
            return

        table = self.query_one("#keybindings-table", DataTable)
        table.clear()

        for key, action in sorted(
            self._keybindings.bindings.items(), key=lambda x: x[1].name
        ):
            # Format key for display
            display_key = key.replace("ctrl+", "C-").replace("shift+", "S-")
            table.add_row(display_key, action.name.replace("_", " ").title())

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        self.query_one("#keybindings-table", DataTable).action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        self.query_one("#keybindings-table", DataTable).action_cursor_up()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "clear-cache":
            self.post_message(self.CacheCleared())
        elif event.button.id == "reauth":
            self.post_message(self.AuthRefresh())

    def on_settings_view_cache_cleared(self, event: CacheCleared) -> None:
        """Forward to app."""
        self.app.post_message(event)

    def on_settings_view_auth_refresh(self, event: AuthRefresh) -> None:
        """Forward to app."""
        self.app.post_message(event)

    def action_noop(self) -> None:
        """No-op for view switch key."""
        pass
