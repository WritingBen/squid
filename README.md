# Squid

A CMUS-inspired terminal frontend for YouTube Music built with Python and Textual.

## Features

- **7 Views** (like CMUS):
  1. Library Tree - Artist/Album hierarchy
  2. Library Sorted - Flat sorted track list
  3. Playlists - YouTube Music playlists
  4. Queue - Current play queue with reordering
  5. Now Playing - Large format current track
  6. Search - Search YouTube Music
  7. Settings - Keybindings and config

- **Vim-style Navigation**
- **MPV Audio Backend**
- **OAuth Authentication**
- **SQLite Caching**

## Requirements

- Python 3.11+
- MPV (for audio playback)
- A YouTube Music account

## Installation

```bash
# Install MPV (if not installed)
# Arch Linux
sudo pacman -S mpv

# Ubuntu/Debian
sudo apt install mpv

# macOS
brew install mpv

# Install Squid
cd /path/to/Squid
pip install -e .
```

## Authentication

Before using Squid, you need to authenticate with YouTube Music:

```bash
squid --auth
```

This will open a browser window for OAuth authentication. Your credentials will be stored in `~/.config/squid/oauth.json`.

## Usage

```bash
squid
```

## Keybindings

### Navigation
| Key | Action |
|-----|--------|
| `j` / `k` | Move down / up |
| `g` / `G` | Go to top / bottom |
| `h` / `l` | Collapse / expand (tree), Seek backward / forward |
| `Enter` | Select / Play |

### Views
| Key | View |
|-----|------|
| `1` | Library Tree |
| `2` | Library Sorted |
| `3` | Playlists |
| `4` | Queue |
| `5` | Now Playing |
| `6` | Search |
| `7` | Settings |

### Playback
| Key | Action |
|-----|--------|
| `c` | Play / Pause |
| `v` | Stop |
| `b` | Next track |
| `z` | Previous track |
| `+` / `-` | Volume up / down |
| `m` | Mute |
| `s` | Toggle shuffle |
| `r` | Cycle repeat mode |

### Queue
| Key | Action |
|-----|--------|
| `a` | Add to queue |
| `A` | Add next |
| `d` | Remove from queue |
| `D` | Clear queue |
| `J` / `K` | Move track down / up |

### Command Mode
| Key | Action |
|-----|--------|
| `:` | Enter command mode |
| `/` | Enter search mode |
| `Escape` | Cancel |
| `q` | Quit |

## Commands

Enter command mode with `:` and type:

| Command | Description |
|---------|-------------|
| `quit` or `q` | Quit Squid |
| `volume <0-100>` | Set volume |
| `seek <seconds>` | Seek to position |
| `shuffle` | Toggle shuffle |
| `repeat` | Cycle repeat mode |
| `clear` | Clear queue |
| `refresh` | Reload library |
| `cache clear` | Clear API cache |
| `help` | Show settings |

## Configuration

Configuration files are stored in:
- Config: `~/.config/squid/`
- Cache: `~/.cache/squid/`
- Data: `~/.local/share/squid/`

## Tech Stack

- **TUI Framework:** Textual
- **YouTube Music API:** ytmusicapi
- **Stream Extraction:** yt-dlp
- **Audio Playback:** MPV (via python-mpv)
- **Data Models:** Pydantic

## License

MIT
