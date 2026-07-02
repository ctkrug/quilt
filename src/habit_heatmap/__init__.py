"""habit-heatmap: render GitHub-style contribution heatmaps from any CSV of dated events."""

from .parser import load_events
from .render_svg import render_svg
from .version import __version__

__all__ = ["load_events", "render_svg", "__version__"]
