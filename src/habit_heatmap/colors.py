"""Color scales for mapping event intensity to heatmap cell colors."""

from __future__ import annotations

from bisect import bisect_right
from collections.abc import Sequence
from math import isfinite
from numbers import Real

# GitHub classic green scale, lightest to darkest.
GITHUB_GREEN = ("#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39")

THEMES: dict[str, tuple[str, ...]] = {
    "github": GITHUB_GREEN,
    "blue": ("#ebedf0", "#c6dbef", "#6baed6", "#3182bd", "#08519c"),
    "purple": ("#ebedf0", "#dadaeb", "#9e9ac8", "#6a51a3", "#3f007d"),
    "mono": ("#ebedf0", "#c4c4c4", "#8c8c8c", "#545454", "#1a1a1a"),
    "dark": ("#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"),
}


def resolve_steps(
    max_value: float,
    steps: Sequence[float] | None = None,
) -> tuple[float, float, float, float]:
    """Resolve four color-change thresholds for a five-color palette.

    With no custom values, preserve Quilt's original automatic scale:
    the boundaries are 0, one quarter, one half, and three quarters of
    the in-range maximum. Zero and negative values remain in the lightest
    color; positive values move through the palette at the other boundaries.

    A supplied sequence must contain exactly four positive, finite,
    strictly increasing absolute threshold values. These are the actual
    values where the color changes, not interval widths or increments.
    """
    if steps is None:
        width = max_value / 4 if max_value > 0 else 0.0
        return (0.0, width, 2 * width, 3 * width)

    if isinstance(steps, (str, bytes)) or not isinstance(steps, Sequence):
        raise ValueError(
            "steps must be a sequence of exactly four positive, "
            "finite, strictly increasing thresholds"
        )
    if len(steps) != 4:
        raise ValueError("steps must contain exactly four thresholds")

    if any(isinstance(value, bool) or not isinstance(value, Real) for value in steps):
        raise ValueError("all step thresholds must be numeric")

    thresholds = tuple(float(value) for value in steps)
    if not all(isfinite(value) and value > 0 for value in thresholds):
        raise ValueError("all step thresholds must be positive and finite")
    if not all(left < right for left, right in zip(thresholds, thresholds[1:])):
        raise ValueError("step thresholds must be strictly increasing")

    return thresholds


def color_for_steps(
    value: float,
    thresholds: Sequence[float],
    palette: tuple[str, ...],
) -> str:
    """Map a value to a palette color using four absolute thresholds.

    Values at or below zero use the lightest color. Otherwise, each threshold
    moves the value to the next palette color when reached (inclusive).
    """
    if value <= 0:
        return palette[0]

    index = bisect_right(thresholds, value)
    return palette[min(index, len(palette) - 1)]


def bucket_color(
    value: float,
    max_value: float,
    palette: tuple[str, ...],
    steps: Sequence[float] | None = None,
) -> str:
    """Map a value to a palette color.

    Without custom steps, use the original automatic scale. With custom
    steps, use exactly four absolute color-change thresholds.
    """
    if steps is None and max_value <= 0:
        return palette[0]

    thresholds = resolve_steps(max_value, steps)
    return color_for_steps(value, thresholds, palette)
