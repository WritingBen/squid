"""Textual screen views."""

from squid.views.library import LibraryTreeView, LibrarySortedView
from squid.views.queue_view import QueueView
from squid.views.now_playing import NowPlayingView
from squid.views.search import SearchView
from squid.views.settings import SettingsView

__all__ = [
    "LibraryTreeView",
    "LibrarySortedView",
    "QueueView",
    "NowPlayingView",
    "SearchView",
    "SettingsView",
]
