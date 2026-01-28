"""Custom Textual widgets."""

from squid.widgets.track_list import TrackList
from squid.widgets.artist_tree import ArtistTree
from squid.widgets.status_bar import StatusBar
from squid.widgets.progress_bar import ProgressBar
from squid.widgets.command_line import CommandLine
from squid.widgets.playbar import PlayBar
from squid.widgets.splitter import VerticalSplitter
from squid.widgets.volume_slider import VolumeSlider
from squid.widgets.resizable_header import ResizableHeader, ColumnDef

__all__ = [
    "TrackList",
    "ArtistTree",
    "StatusBar",
    "ProgressBar",
    "CommandLine",
    "PlayBar",
    "VerticalSplitter",
    "VolumeSlider",
    "ResizableHeader",
    "ColumnDef",
]
