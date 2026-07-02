"""Render a date -> value mapping as a GitHub-style SVG contribution heatmap."""

from __future__ import annotations

from datetime import date, timedelta

from .colors import THEMES, bucket_color

CELL_SIZE = 11
CELL_GAP = 3
MARGIN = 20
WEEKDAY_LABEL_WIDTH = 26
WEEKDAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # Sunday = 0
FONT = "font-family=\"sans-serif\" font-size=\"9\" fill=\"#767676\""


def _week_start(day: date) -> date:
    """Return the Sunday on or before ``day`` (weeks run Sun-Sat, GitHub-style)."""
    return day - timedelta(days=(day.weekday() + 1) % 7)


def render_svg(
    counts: dict[date, float],
    start: date | None = None,
    end: date | None = None,
    theme: str = "github",
    cell_size: int = CELL_SIZE,
    gap: int = CELL_GAP,
) -> str:
    """Render ``counts`` as a self-contained SVG contribution heatmap.

    Defaults to spanning the earliest to latest date present in
    ``counts``; pass ``start``/``end`` to render an explicit range
    (required if ``counts`` is empty).
    """
    if not counts and (start is None or end is None):
        raise ValueError("counts is empty; pass explicit start and end dates")

    end = end or max(counts)
    start = start or min(counts)
    if start > end:
        raise ValueError("start date must be on or before end date")

    palette = THEMES.get(theme, THEMES["github"])
    max_value = max(counts.values()) if counts else 0.0

    grid_start = _week_start(start)
    total_days = (end - grid_start).days + 1
    weeks = (total_days + 6) // 7

    stride = cell_size + gap
    grid_x0 = MARGIN + WEEKDAY_LABEL_WIDTH
    grid_y0 = MARGIN
    width = grid_x0 + weeks * stride + MARGIN
    height = grid_y0 + 7 * stride + MARGIN

    cells = []
    day = grid_start
    while day <= end:
        if day >= start:
            week_index = (day - grid_start).days // 7
            weekday = (day.weekday() + 1) % 7  # Sunday = 0
            x = grid_x0 + week_index * stride
            y = grid_y0 + weekday * stride
            value = counts.get(day, 0.0)
            color = bucket_color(value, max_value, palette)
            cells.append(
                f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                f'rx="2" ry="2" fill="{color}"><title>{day.isoformat()}: {value:g}</title></rect>'
            )
        day += timedelta(days=1)

    labels = [
        f'<text x="{MARGIN}" y="{grid_y0 + weekday * stride + cell_size - 1}" {FONT}>{text}</text>'
        for weekday, text in WEEKDAY_LABELS.items()
    ]

    body = "\n  ".join(labels + cells)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n  {body}\n</svg>\n'
    )
