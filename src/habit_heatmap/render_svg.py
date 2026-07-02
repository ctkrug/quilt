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
WEEK_START_WEEKDAYS = {"sunday": 6, "monday": 0}  # date.weekday(): Monday=0 ... Sunday=6
WEEKDAY_LABEL_TEXT = {0: "Mon", 2: "Wed", 4: "Fri"}  # date.weekday() of each labeled day
MONTH_NAMES = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)
FONT = "font-family=\"sans-serif\" font-size=\"9\" fill=\"#767676\""
TITLE_FONT = 'font-family="sans-serif" font-size="14" font-weight="600" fill="#24292f"'


def _week_start(day: date, start_weekday: int) -> date:
    """Return the first day of ``day``'s week, where a week begins on
    ``start_weekday`` (Python's ``date.weekday()`` numbering: Monday=0)."""
    return day - timedelta(days=(day.weekday() - start_weekday) % 7)


def _weekday_labels(start_weekday: int, grid_y0: int, stride: int, cell_size: int) -> list[str]:
    """Build the Mon/Wed/Fri labels beside the grid, positioned by row."""
    labels = []
    for py_weekday, text in WEEKDAY_LABEL_TEXT.items():
        row = (py_weekday - start_weekday) % 7
        y = grid_y0 + row * stride + cell_size - 1
        labels.append(f'<text x="{MARGIN}" y="{y}" {FONT}>{text}</text>')
    return labels


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
    week_start: str = "sunday",
) -> str:
    """Render ``counts`` as a self-contained SVG contribution heatmap.

    Defaults to spanning the earliest to latest date present in
    ``counts``; pass ``start``/``end`` to render an explicit range
    (required if ``counts`` is empty). Pass ``legend=False`` to omit the
    "Less ... More" color-scale strip below the grid, or ``label`` to
    render a title above the chart. ``week_start`` is ``"sunday"``
    (GitHub-style) or ``"monday"`` (ISO week convention).
    """
    if not counts and (start is None or end is None):
        raise ValueError("counts is empty; pass explicit start and end dates")
    if week_start not in WEEK_START_WEEKDAYS:
        raise ValueError(f"week_start must be one of {sorted(WEEK_START_WEEKDAYS)}")

    end = end or max(counts)
    start = start or min(counts)
    if start > end:
        raise ValueError("start date must be on or before end date")

    palette = THEMES.get(theme, THEMES["github"])
    max_value = max(counts.values()) if counts else 0.0
    start_weekday = WEEK_START_WEEKDAYS[week_start]

    grid_start = _week_start(start, start_weekday)
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
            weekday = (day.weekday() - start_weekday) % 7
            x = grid_x0 + week_index * stride
            y = grid_y0 + weekday * stride
            value = counts.get(day, 0.0)
            color = bucket_color(value, max_value, palette)
            cells.append(
                f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                f'rx="2" ry="2" fill="{color}"><title>{day.isoformat()}: {value:g}</title></rect>'
            )
        day += timedelta(days=1)

    weekday_labels = _weekday_labels(start_weekday, grid_y0, stride, cell_size)
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
