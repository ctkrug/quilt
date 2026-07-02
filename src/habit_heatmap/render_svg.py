"""Render a date -> value mapping as a GitHub-style SVG contribution heatmap."""

from __future__ import annotations

from datetime import date, timedelta
from xml.sax.saxutils import escape

from .colors import THEMES, bucket_color

CELL_SIZE = 11
CELL_GAP = 3
MARGIN = 20
WEEKDAY_LABEL_WIDTH = 26
MONTH_LABEL_HEIGHT = 16
MONTH_LABEL_MIN_GAP_WEEKS = 2
LEGEND_HEIGHT = 20
LEGEND_LESS_WIDTH = 24
LEGEND_MORE_WIDTH = 28
LEGEND_SWATCH_GAP = 2
TITLE_HEIGHT = 22
WEEKDAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # Sunday = 0
MONTH_NAMES = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)
FONT = "font-family=\"sans-serif\" font-size=\"9\" fill=\"#767676\""
TITLE_FONT = 'font-family="sans-serif" font-size="14" font-weight="600" fill="#24292f"'


def _week_start(day: date) -> date:
    """Return the Sunday on or before ``day`` (weeks run Sun-Sat, GitHub-style)."""
    return day - timedelta(days=(day.weekday() + 1) % 7)


def _month_labels(
    grid_start: date, start: date, weeks: int, stride: int, x0: int, y: int
) -> list[str]:
    """Build a month-name label for each week column where a new month begins.

    The leading week may start before ``start`` (grid weeks are padded out
    to a full Sun-Sat row), so its label uses ``start``'s month rather than
    the padding days'. Skips a label that would land within
    ``MONTH_LABEL_MIN_GAP_WEEKS`` of the previous one, so short months don't
    produce overlapping text.
    """
    labels = []
    last_labeled_week = -MONTH_LABEL_MIN_GAP_WEEKS
    last_month = None
    for week_index in range(weeks):
        sunday = grid_start + timedelta(weeks=week_index)
        month = start.month if week_index == 0 else sunday.month
        if month == last_month:
            continue
        last_month = month
        if week_index - last_labeled_week < MONTH_LABEL_MIN_GAP_WEEKS:
            continue
        last_labeled_week = week_index
        x = x0 + week_index * stride
        labels.append(f'<text x="{x}" y="{y}" {FONT}>{MONTH_NAMES[month - 1]}</text>')
    return labels


def _legend(palette: tuple[str, ...], x0: int, y: int, cell_size: int) -> list[str]:
    """Build a "Less ... More" legend strip using ``palette``'s own colors."""
    elements = [f'<text x="{x0}" y="{y + cell_size - 1}" {FONT}>Less</text>']
    swatch_x = x0 + LEGEND_LESS_WIDTH
    stride = cell_size + LEGEND_SWATCH_GAP
    for color in palette:
        elements.append(
            f'<rect x="{swatch_x}" y="{y}" width="{cell_size}" height="{cell_size}" '
            f'rx="2" ry="2" fill="{color}"/>'
        )
        swatch_x += stride
    elements.append(f'<text x="{swatch_x}" y="{y + cell_size - 1}" {FONT}>More</text>')
    return elements


def render_svg(
    counts: dict[date, float],
    start: date | None = None,
    end: date | None = None,
    theme: str = "github",
    cell_size: int = CELL_SIZE,
    gap: int = CELL_GAP,
    legend: bool = True,
    label: str | None = None,
) -> str:
    """Render ``counts`` as a self-contained SVG contribution heatmap.

    Defaults to spanning the earliest to latest date present in
    ``counts``; pass ``start``/``end`` to render an explicit range
    (required if ``counts`` is empty). Pass ``legend=False`` to omit the
    "Less ... More" color-scale strip below the grid, or ``label`` to
    render a title above the chart.
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
    grid_y0 = MARGIN + (TITLE_HEIGHT if label else 0) + MONTH_LABEL_HEIGHT
    width = grid_x0 + weeks * stride + MARGIN
    height = grid_y0 + 7 * stride + (LEGEND_HEIGHT if legend else 0) + MARGIN

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

    weekday_labels = [
        f'<text x="{MARGIN}" y="{grid_y0 + weekday * stride + cell_size - 1}" {FONT}>{text}</text>'
        for weekday, text in WEEKDAY_LABELS.items()
    ]
    month_labels = _month_labels(grid_start, start, weeks, stride, grid_x0, grid_y0 - 4)
    legend_elements = (
        _legend(palette, grid_x0, grid_y0 + 7 * stride + (LEGEND_HEIGHT - cell_size), cell_size)
        if legend
        else []
    )
    title = (
        [f'<text x="{MARGIN}" y="{MARGIN + 14}" {TITLE_FONT}>{escape(label)}</text>']
        if label
        else []
    )

    body = "\n  ".join(title + weekday_labels + month_labels + cells + legend_elements)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n  {body}\n</svg>\n'
    )
