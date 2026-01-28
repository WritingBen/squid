"""Default keybindings configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class Action(Enum):
    """Available actions."""

    # Navigation
    CURSOR_UP = auto()
    CURSOR_DOWN = auto()
    SCROLL_HOME = auto()
    SCROLL_END = auto()
    PAGE_UP = auto()
    PAGE_DOWN = auto()

    # Views
    VIEW_LIBRARY_TREE = auto()
    VIEW_LIBRARY_SORTED = auto()
    VIEW_PLAYLISTS = auto()
    VIEW_QUEUE = auto()
    VIEW_NOW_PLAYING = auto()
    VIEW_SEARCH = auto()
    VIEW_SETTINGS = auto()

    # Playback
    PLAY_PAUSE = auto()
    STOP = auto()
    NEXT_TRACK = auto()
    PREV_TRACK = auto()
    SEEK_FORWARD = auto()
    SEEK_BACKWARD = auto()
    SEEK_FORWARD_LARGE = auto()
    SEEK_BACKWARD_LARGE = auto()

    # Volume
    VOLUME_UP = auto()
    VOLUME_DOWN = auto()
    MUTE = auto()

    # Modes
    TOGGLE_SHUFFLE = auto()
    CYCLE_REPEAT = auto()

    # Selection
    SELECT = auto()
    ADD_TO_QUEUE = auto()
    ADD_TO_QUEUE_NEXT = auto()
    REMOVE_FROM_QUEUE = auto()

    # Command/Search
    COMMAND_MODE = auto()
    SEARCH_MODE = auto()
    CANCEL = auto()

    # Queue manipulation
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    CLEAR_QUEUE = auto()

    # Other
    REFRESH = auto()
    QUIT = auto()
    HELP = auto()


DEFAULT_BINDINGS: dict[str, Action] = {
    # Navigation
    "j": Action.CURSOR_DOWN,
    "k": Action.CURSOR_UP,
    "g": Action.SCROLL_HOME,
    "G": Action.SCROLL_END,
    "ctrl+d": Action.PAGE_DOWN,
    "ctrl+u": Action.PAGE_UP,

    # Views (1-7 like CMUS)
    "1": Action.VIEW_LIBRARY_TREE,
    "2": Action.VIEW_LIBRARY_SORTED,
    "3": Action.VIEW_PLAYLISTS,
    "4": Action.VIEW_QUEUE,
    "5": Action.VIEW_NOW_PLAYING,
    "6": Action.VIEW_SEARCH,
    "7": Action.VIEW_SETTINGS,

    # Playback
    "c": Action.PLAY_PAUSE,
    "v": Action.STOP,
    "b": Action.NEXT_TRACK,
    "z": Action.PREV_TRACK,
    "l": Action.SEEK_FORWARD,
    "h": Action.SEEK_BACKWARD,
    "right": Action.SEEK_FORWARD,
    "left": Action.SEEK_BACKWARD,
    "L": Action.SEEK_FORWARD_LARGE,
    "H": Action.SEEK_BACKWARD_LARGE,

    # Volume
    "+": Action.VOLUME_UP,
    "=": Action.VOLUME_UP,  # For convenience (no shift needed)
    "-": Action.VOLUME_DOWN,
    "m": Action.MUTE,

    # Modes
    "s": Action.TOGGLE_SHUFFLE,
    "r": Action.CYCLE_REPEAT,

    # Selection
    "enter": Action.SELECT,
    "a": Action.ADD_TO_QUEUE,
    "A": Action.ADD_TO_QUEUE_NEXT,
    "d": Action.REMOVE_FROM_QUEUE,
    "D": Action.CLEAR_QUEUE,

    # Command/Search
    ":": Action.COMMAND_MODE,
    "/": Action.SEARCH_MODE,
    "escape": Action.CANCEL,

    # Queue manipulation
    "K": Action.MOVE_UP,
    "J": Action.MOVE_DOWN,

    # Other
    "R": Action.REFRESH,
    "q": Action.QUIT,
    "?": Action.HELP,
}


@dataclass
class Keybindings:
    """Keybindings configuration."""

    bindings: dict[str, Action] = field(default_factory=lambda: DEFAULT_BINDINGS.copy())

    def get_action(self, key: str) -> Action | None:
        """Get action for a key."""
        return self.bindings.get(key)

    def set_binding(self, key: str, action: Action) -> None:
        """Set a keybinding."""
        self.bindings[key] = action

    def remove_binding(self, key: str) -> None:
        """Remove a keybinding."""
        self.bindings.pop(key, None)

    def get_keys_for_action(self, action: Action) -> list[str]:
        """Get all keys bound to an action."""
        return [key for key, act in self.bindings.items() if act == action]

    def to_dict(self) -> dict[str, str]:
        """Serialize to dict."""
        return {key: action.name for key, action in self.bindings.items()}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Keybindings:
        """Deserialize from dict."""
        bindings = {}
        for key, action_name in data.items():
            try:
                bindings[key] = Action[action_name]
            except KeyError:
                pass
        return cls(bindings=bindings)
