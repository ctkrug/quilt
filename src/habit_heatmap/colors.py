"""Color scales for mapping event intensity to heatmap cell colors."""

from __future__ import annotations

# GitHub's classic green scale, lightest (no activity) to darkest.
GITHUB_GREEN = ("#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39")

THEMES: dict[str, tuple[str, ...]] = {
    "github": GITHUB_GREEN,
    "blue": ("#ebedf0", "#c6dbef", "#6baed6", "#3182bd", "#08519c"),
    "purple": ("#ebedf0", "#dadaeb", "#9e9ac8", "#6a51a3", "#3f007d"),
}


def bucket_color(value: float, max_value: float, palette: tuple[str, ...]) -> str:
    """Map ``value`` into one of ``palette``'s intensity buckets.

    ``max_value`` anchors the scale (typically the largest value in the
    dataset being rendered), so the darkest color is reserved for the
    single busiest day.
    """
    if value <= 0 or max_value <= 0:
        return palette[0]
    step = max_value / (len(palette) - 1)
    index = min(len(palette) - 1, int(value / step) + 1)
    return palette[index]
