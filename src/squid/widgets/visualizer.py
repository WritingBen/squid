"""Beat-reactive audio visualizer widget."""

from __future__ import annotations

import math
import random
from enum import Enum, auto
from typing import TYPE_CHECKING

from rich.text import Text
from textual.reactive import reactive
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Static
from textual.app import ComposeResult

if TYPE_CHECKING:
    from squid.player.state import PlaybackState


class VisualizerMode(Enum):
    """Available visualization modes."""

    SPECTRUM = auto()
    WAVE = auto()
    PARTICLES = auto()
    GEOMETRIC = auto()


class Visualizer(Widget):
    """Beat-reactive audio visualizer widget.

    Uses simulated beat detection based on:
    - Pseudo-random beat events at musically plausible intervals
    - Volume level scaling from PlaybackState
    - Smooth interpolation for natural-looking animations
    """

    DEFAULT_CSS = """
    Visualizer {
        width: 100%;
        height: 8;
        border: round ansi_magenta;
        padding: 0 1;
    }

    Visualizer .visualizer-canvas {
        width: 100%;
        height: 100%;
    }
    """

    mode: reactive[VisualizerMode] = reactive(VisualizerMode.SPECTRUM)
    is_playing: reactive[bool] = reactive(False)
    volume: reactive[int] = reactive(100)

    FPS = 15
    BEAT_MIN_INTERVAL = 0.3
    BEAT_MAX_INTERVAL = 0.8

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._timer: Timer | None = None
        self._frame: int = 0

        # Beat simulation state
        self._beat_energy: float = 0.0
        self._next_beat_time: float = 0.0
        self._time_elapsed: float = 0.0

        # Mode-specific state
        self._spectrum_bars: list[float] = []
        self._wave_offset: float = 0.0
        self._particles: list[dict] = []
        self._geo_scale: float = 0.5

    def compose(self) -> ComposeResult:
        yield Static("", id="canvas", classes="visualizer-canvas")

    def on_mount(self) -> None:
        """Start animation timer when mounted."""
        self._init_state()
        if self.is_playing:
            self._start_animation()

    def on_unmount(self) -> None:
        """Stop animation timer when unmounted."""
        self._stop_animation()

    def on_resize(self) -> None:
        """Reinitialize state on resize."""
        self._init_state()

    def _init_state(self) -> None:
        """Initialize mode-specific state based on widget size."""
        width = max(10, self.size.width - 4)

        num_bars = max(8, width // 3)
        self._spectrum_bars = [0.0] * num_bars
        self._particles = []
        self._next_beat_time = random.uniform(0.1, 0.3)

    def _start_animation(self) -> None:
        """Start the animation timer."""
        if self._timer is None:
            interval = 1.0 / self.FPS
            # Use app-level timer with closure (bound methods don't work reliably)
            viz = self
            def do_animate():
                if not viz.is_playing:
                    return
                dt = 1.0 / viz.FPS
                viz._time_elapsed += dt
                viz._frame += 1
                viz._update_beat(dt)
                if viz.mode == VisualizerMode.SPECTRUM:
                    viz._update_spectrum(dt)
                    viz._render_spectrum()
                elif viz.mode == VisualizerMode.WAVE:
                    viz._update_wave(dt)
                    viz._render_wave()
                elif viz.mode == VisualizerMode.PARTICLES:
                    viz._update_particles(dt)
                    viz._render_particles()
                elif viz.mode == VisualizerMode.GEOMETRIC:
                    viz._update_geometric(dt)
                    viz._render_geometric()
                viz.refresh()
            self._timer = self.app.set_interval(interval, do_animate)

    def _stop_animation(self) -> None:
        """Stop the animation timer."""
        if self._timer:
            self._timer.stop()
            self._timer = None

    def watch_is_playing(self, playing: bool) -> None:
        """Start/stop animation based on playback state."""
        if playing:
            self._start_animation()
        else:
            self._stop_animation()
            self._render_stopped()

    def watch_mode(self, mode: VisualizerMode) -> None:
        """Reset state when mode changes."""
        self._init_state()

    def _animate(self) -> None:
        """Main animation loop."""
        if not self.is_playing:
            return

        dt = 1.0 / self.FPS
        self._time_elapsed += dt
        self._frame += 1

        self._update_beat(dt)

        if self.mode == VisualizerMode.SPECTRUM:
            self._update_spectrum(dt)
            self._render_spectrum()
        elif self.mode == VisualizerMode.WAVE:
            self._update_wave(dt)
            self._render_wave()
        elif self.mode == VisualizerMode.PARTICLES:
            self._update_particles(dt)
            self._render_particles()
        elif self.mode == VisualizerMode.GEOMETRIC:
            self._update_geometric(dt)
            self._render_geometric()

    def _update_beat(self, dt: float) -> None:
        """Simulate beat detection with controlled randomness."""
        self._beat_energy *= 0.85

        if self._time_elapsed >= self._next_beat_time:
            volume_factor = self.volume / 100.0
            self._beat_energy = 0.7 + (random.random() * 0.3)
            self._beat_energy *= volume_factor

            interval = random.uniform(self.BEAT_MIN_INTERVAL, self.BEAT_MAX_INTERVAL)
            self._next_beat_time = self._time_elapsed + interval

    def cycle_mode(self) -> VisualizerMode:
        """Cycle to next visualization mode."""
        modes = list(VisualizerMode)
        current_idx = modes.index(self.mode)
        self.mode = modes[(current_idx + 1) % len(modes)]
        return self.mode

    def update_from_state(self, state: PlaybackState) -> None:
        """Update visualizer from playback state."""
        from squid.player.state import PlayerState

        self.is_playing = state.state == PlayerState.PLAYING
        self.volume = state.volume

    def _render_stopped(self) -> None:
        """Render a static stopped state."""
        canvas = self.query_one("#canvas", Static)
        height = max(1, self.size.height - 2)
        width = max(10, self.size.width - 4)

        mode_name = self.mode.name.title()
        lines = []
        for row in range(height):
            if row == height // 2:
                padding = (width - len(mode_name)) // 2
                lines.append(" " * padding + mode_name)
            else:
                lines.append("")
        text = Text("\n".join(lines), style="bright_black")
        canvas.update(text)

    # --- Spectrum Mode ---

    def _update_spectrum(self, dt: float) -> None:
        """Update spectrum bar heights."""
        for i in range(len(self._spectrum_bars)):
            target = random.random() * 0.4 + 0.1

            if self._beat_energy > 0.3:
                freq_factor = 1.0 - abs(i - len(self._spectrum_bars) // 2) / len(
                    self._spectrum_bars
                )
                target += self._beat_energy * freq_factor * 0.6

            self._spectrum_bars[i] += (target - self._spectrum_bars[i]) * 0.3

    def _render_spectrum(self) -> None:
        """Render spectrum bars as vertical equalizer."""
        canvas = self.query_one("#canvas", Static)
        height = max(1, self.size.height - 2)
        width = max(10, self.size.width - 4)

        bar_chars = "▁▂▃▄▅▆▇█"
        num_bars = len(self._spectrum_bars)
        bar_width = max(1, width // num_bars)

        text = Text()
        for row in range(height):
            row_from_bottom = height - 1 - row
            for i, bar_height in enumerate(self._spectrum_bars):
                filled_height = int(bar_height * height)
                if row_from_bottom < filled_height:
                    char_idx = min(7, int(bar_height * 8))
                    char = bar_chars[char_idx]
                    if row_from_bottom > height * 0.7:
                        style = "magenta"
                    elif row_from_bottom > height * 0.4:
                        style = "cyan"
                    else:
                        style = "blue"
                    text.append(char * bar_width, style=style)
                else:
                    text.append(" " * bar_width)
            if row < height - 1:
                text.append("\n")

        canvas.update(text)

    # --- Wave Mode ---

    def _update_wave(self, dt: float) -> None:
        """Update wave offset for animation."""
        self._wave_offset += dt * 3.0
        if self._beat_energy > 0.3:
            self._wave_offset += self._beat_energy * 0.5

    def _render_wave(self) -> None:
        """Render horizontal wave emanating from center."""
        canvas = self.query_one("#canvas", Static)
        height = max(1, self.size.height - 2)
        width = max(10, self.size.width - 4)
        center_y = height // 2
        center_x = width // 2

        wave_chars = " .:-=+*#%@"
        text = Text()

        for row in range(height):
            for col in range(width):
                dx = col - center_x
                dy = (row - center_y) * 2
                dist = math.sqrt(dx * dx + dy * dy)

                wave_val = math.sin(dist * 0.5 - self._wave_offset)
                wave_val = (wave_val + 1) / 2
                wave_val *= 0.5 + self._beat_energy * 0.5

                char_idx = int(wave_val * (len(wave_chars) - 1))
                char = wave_chars[char_idx]

                if dist < 5:
                    style = "bright_white"
                elif dist < 15:
                    style = "cyan"
                else:
                    style = "blue"

                text.append(char, style=style)
            if row < height - 1:
                text.append("\n")

        canvas.update(text)

    # --- Particles Mode ---

    def _update_particles(self, dt: float) -> None:
        """Update particle positions and spawn new ones on beats."""
        width = max(10, self.size.width - 4)
        height = max(1, self.size.height - 2)

        if self._beat_energy > 0.5:
            num_new = int(self._beat_energy * 5)
            for _ in range(num_new):
                self._particles.append(
                    {
                        "x": width // 2 + random.randint(-3, 3),
                        "y": height // 2,
                        "vx": random.uniform(-2, 2),
                        "vy": random.uniform(-1.5, 1.5),
                        "char": random.choice("*+.oO@#"),
                        "life": 1.0,
                        "style": random.choice(["cyan", "magenta", "yellow", "white"]),
                    }
                )

        new_particles = []
        for p in self._particles:
            p["x"] += p["vx"] * dt * 10
            p["y"] += p["vy"] * dt * 10
            p["life"] -= dt * 0.5

            if p["life"] > 0 and 0 <= p["x"] < width and 0 <= p["y"] < height:
                new_particles.append(p)

        self._particles = new_particles

    def _render_particles(self) -> None:
        """Render particle field."""
        canvas = self.query_one("#canvas", Static)
        height = max(1, self.size.height - 2)
        width = max(10, self.size.width - 4)

        grid = [[(" ", "default") for _ in range(width)] for _ in range(height)]

        for p in self._particles:
            x, y = int(p["x"]), int(p["y"])
            if 0 <= x < width and 0 <= y < height:
                if p["life"] > 0.7:
                    char = p["char"]
                elif p["life"] > 0.4:
                    char = "."
                else:
                    char = " "
                grid[y][x] = (char, p["style"])

        text = Text()
        for row_idx, row in enumerate(grid):
            for char, style in row:
                text.append(char, style=style)
            if row_idx < height - 1:
                text.append("\n")

        canvas.update(text)

    # --- Geometric Mode ---

    def _update_geometric(self, dt: float) -> None:
        """Update geometric shape scale."""
        target_scale = 0.3 + self._beat_energy * 0.7
        self._geo_scale += (target_scale - self._geo_scale) * 0.2
        self._geo_scale = max(0.1, min(1.0, self._geo_scale))

    def _render_geometric(self) -> None:
        """Render pulsing geometric shapes."""
        canvas = self.query_one("#canvas", Static)
        height = max(1, self.size.height - 2)
        width = max(10, self.size.width - 4)
        center_x = width // 2
        center_y = height // 2

        text = Text()

        for row in range(height):
            for col in range(width):
                dx = abs(col - center_x)
                dy = abs(row - center_y) * 2

                dist = dx + dy
                max_dist = (width // 2 + height) * self._geo_scale

                ring_spacing = max(2, int(max_dist / 4))
                ring_pos = dist % ring_spacing

                if dist < max_dist:
                    if ring_pos < 2:
                        char = "\u2588"
                        ring_num = dist // ring_spacing
                        colors = ["magenta", "cyan", "blue", "bright_black"]
                        style = colors[int(ring_num) % len(colors)]
                    else:
                        char = " "
                        style = "default"
                else:
                    char = " "
                    style = "default"

                text.append(char, style=style)
            if row < height - 1:
                text.append("\n")

        canvas.update(text)
