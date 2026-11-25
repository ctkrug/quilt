"""Render a date -> value mapping as a GitHub-style SVG contribution heatmap."""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import date, timedelta
from math import isfinite
from numbers import Real
from xml.sax.saxutils import escape

from .colors import THEMES, color_for_steps, resolve_steps

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
FONT = 'font-family="sans-serif" font-size="9" fill="#767676"'


def _week_start(day: date, start_weekday: int) -> date:
    """Return the first day of ``day``'s week, where a week begins on
    ``start_weekday`` (Python's ``date.weekday()`` numbering: Monday=0)."""
    return day - timedelta(days=(day.weekday() - start_weekday) % 7)


def _label_style(
    font_size: int | float,
    color: str,
    label_type: str,
    *,
    font_weight: str | None = None,
) -> str:
    """Validate and build an SVG text style for a text element."""
    if (
        isinstance(font_size, bool)
        or not isinstance(font_size, Real)
        or not isfinite(float(font_size))
        or font_size <= 0
    ):
        raise ValueError(f"{label_type} font size must be a positive finite number")
    if (
        not isinstance(color, str)
        or re.fullmatch(
            r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?",
            color,
        )
        is None
    ):
        raise ValueError(
            f"{label_type} color must be a 3- or 6-digit hex color "
            "(e.g. #8b949e)"
        )
    weight = f' font-weight="{escape(font_weight)}"' if font_weight else ""
    return (
        f'font-family="sans-serif" font-size="{float(font_size):g}"'
        f'{weight} fill="{escape(color)}"'
    )


def _default_label_color(theme: str) -> str:
    """Choose a readable label color from the theme background luminance."""
    background = THEMES[theme][0]
    channels = tuple(
        int(background[index : index + 2], 16) / 255
        for index in (1, 3, 5)
    )
    linear = tuple(
        channel / 12.92 if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    )
    luminance = 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
    return "#FFFFFF" if luminance < 0.5 else "#767676"


def _weekday_labels(
    start_weekday: int,
    grid_y0: int,
    stride: int,
    cell_size: int,
    font_style: str = FONT,
) -> list[str]:
    """Build the Mon/Wed/Fri labels beside the grid, positioned by row."""
    labels = []
    for py_weekday, text in WEEKDAY_LABEL_TEXT.items():
        row = (py_weekday - start_weekday) % 7
        y = grid_y0 + row * stride + cell_size - 1
        labels.append(f'<text x="{MARGIN}" y="{y}" {font_style}>{text}</text>')
    return labels


def _month_labels(
    grid_start: date,
    start: date,
    weeks: int,
    stride: int,
    x0: int,
    y: int,
    font_style: str = FONT,
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
        labels.append(f'<text x="{x}" y="{y}" {font_style}>{MONTH_NAMES[month - 1]}</text>')
    return labels


def _legend(
    palette: tuple[str, ...],
    x0: int,
    y: int,
    cell_size: int,
    font_style: str = FONT,
) -> list[str]:
    """Build a "Less ... More" legend strip using ``palette``'s own colors."""
    elements = [f'<text x="{x0}" y="{y + cell_size - 1}" {font_style}>Less</text>']
    swatch_x = x0 + LEGEND_LESS_WIDTH
    stride = cell_size + LEGEND_SWATCH_GAP
    for color in palette:
        elements.append(
            f'<rect x="{swatch_x}" y="{y}" width="{cell_size}" height="{cell_size}" '
            f'rx="2" ry="2" fill="{color}"/>'
        )
        swatch_x += stride
    elements.append(f'<text x="{swatch_x}" y="{y + cell_size - 1}" {font_style}>More</text>')
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
    steps: Sequence[float] | None = None,
    month_label_font_size: int | float = 9,
    month_label_color: str | None = None,
    weekday_label_font_size: int | float = 9,
    weekday_label_color: str | None = None,
    title_font_size: int | float = 14,
    title_color: str | None = None,
    legend_font_size: int | float = 9,
    legend_color: str | None = None,
) -> str:
    """Render ``counts`` as a self-contained SVG contribution heatmap.

    Defaults to spanning the earliest to latest date present in
    ``counts``; pass ``start``/``end`` to render an explicit range
    (required if ``counts`` is empty). Pass ``legend=False`` to omit the
    "Less ... More" color-scale strip below the grid, or ``label`` to
    render a title above the chart. ``week_start`` is ``"sunday"``
    (GitHub-style) or ``"monday"`` (ISO week convention).

    Month, weekday, title, and legend text can be styled independently with their
    respective font-size and color arguments. Font sizes are positive SVG units;
    colors must be 3- or 6-digit hexadecimal strings. Month, weekday, and legend
    font sizes default to 9 SVG units; the title defaults to 14. If a text color
    is omitted, Quilt chooses #767676 for a light theme background or #FFFFFF for
    a dark one. Explicit colors override the theme-aware default for that group.

    ``steps`` controls the intensity scale while keeping the five-color
    palette unchanged:

    * ``None`` (default): preserve the original automatic scaling, with
      four color-change boundaries at zero, one quarter, one half, and three
      quarters of the observed maximum.
    * A sequence of exactly four positive, finite, strictly increasing
      numbers: use these as the exact values where the four color changes occur.

    The supplied thresholds are used directly; they are never interpreted
    as interval widths or added together. Together, the four thresholds divide
    the value range into five color bands. Values below the first threshold use
    the lightest color; reaching each threshold moves the value to the next
    palette color.
    """
    if not counts and (start is None or end is None):
        raise ValueError("counts is empty; pass explicit start and end dates")
    if week_start not in WEEK_START_WEEKDAYS:
        raise ValueError(f"week_start must be one of {sorted(WEEK_START_WEEKDAYS)}")
    if theme not in THEMES:
        raise ValueError(f"theme must be one of {sorted(THEMES)}")

    end = end or max(counts)
    start = start or min(counts)
    if start > end:
        raise ValueError("start date must be on or before end date")

    automatic_label_color = _default_label_color(theme)
    month_label_style = _label_style(
        month_label_font_size,
        automatic_label_color if month_label_color is None else month_label_color,
        "month label",
    )
    weekday_label_style = _label_style(
        weekday_label_font_size,
        automatic_label_color if weekday_label_color is None else weekday_label_color,
        "weekday label",
    )
    title_style = _label_style(
        title_font_size,
        automatic_label_color if title_color is None else title_color,
        "title",
        font_weight="600",
    )
    legend_style = _label_style(
        legend_font_size,
        automatic_label_color if legend_color is None else legend_color,
        "legend",
    )

    palette = THEMES[theme]
    in_range_values = [value for day, value in counts.items() if start <= day <= end]
    max_value = max(in_range_values) if in_range_values else 0.0
    thresholds = resolve_steps(max_value, steps)
    empty_automatic_scale = steps is None and max_value <= 0
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
            color = (
                palette[0]
                if empty_automatic_scale
                else color_for_steps(value, thresholds, palette)
            )
            cells.append(
                f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                f'rx="2" ry="2" fill="{color}"><title>{day.isoformat()}: {value:g}</title></rect>'
            )
        day += timedelta(days=1)

    weekday_labels = _weekday_labels(
        start_weekday, grid_y0, stride, cell_size, weekday_label_style
    )
    month_labels = _month_labels(
        grid_start, start, weeks, stride, grid_x0, grid_y0 - 4, month_label_style
    )
    legend_elements = (
        _legend(
            palette,
            grid_x0,
            grid_y0 + 7 * stride + (LEGEND_HEIGHT - cell_size),
            cell_size,
            legend_style,
        )
        if legend
        else []
    )
    title = (
        [f'<text x="{MARGIN}" y="{MARGIN + 14}" {title_style}>{escape(label)}</text>']
        if label
        else []
    )

    body = "\n  ".join(title + weekday_labels + month_labels + cells + legend_elements)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n  {body}\n</svg>\n'
    )
