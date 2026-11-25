import math

import pytest

from habit_heatmap.colors import THEMES, bucket_color, resolve_steps


def test_bucket_color_zero_value_is_lightest():
    palette = THEMES["github"]
    assert bucket_color(0, 10, palette) == palette[0]


def test_bucket_color_max_value_is_darkest():
    palette = THEMES["github"]
    assert bucket_color(10, 10, palette) == palette[-1]


def test_bucket_color_is_monotonic():
    palette = THEMES["github"]
    low = bucket_color(1, 100, palette)
    high = bucket_color(90, 100, palette)
    assert palette.index(low) < palette.index(high)


def test_bucket_color_handles_zero_max():
    palette = THEMES["github"]
    assert bucket_color(0, 0, palette) == palette[0]


def test_bucket_color_handles_negative_value():
    palette = THEMES["github"]
    assert bucket_color(-5, 10, palette) == palette[0]


def test_default_steps_preserve_four_automatic_color_boundaries():
    assert resolve_steps(100) == (0, 25, 50, 75)


def test_custom_thresholds_are_returned_without_modification():
    assert resolve_steps(999, [5, 20, 50, 100]) == (5, 20, 50, 100)


def test_bucket_color_changes_at_exact_threshold_values():
    palette = THEMES["github"]
    thresholds = [5, 20, 50, 100]

    assert bucket_color(-1, 999, palette, steps=thresholds) == palette[0]
    assert bucket_color(0, 999, palette, steps=thresholds) == palette[0]
    assert bucket_color(4, 999, palette, steps=thresholds) == palette[0]
    assert bucket_color(5, 999, palette, steps=thresholds) == palette[1]
    assert bucket_color(19, 999, palette, steps=thresholds) == palette[1]
    assert bucket_color(20, 999, palette, steps=thresholds) == palette[2]
    assert bucket_color(49, 999, palette, steps=thresholds) == palette[2]
    assert bucket_color(50, 999, palette, steps=thresholds) == palette[3]
    assert bucket_color(99, 999, palette, steps=thresholds) == palette[3]
    assert bucket_color(100, 999, palette, steps=thresholds) == palette[4]
    assert bucket_color(150, 999, palette, steps=thresholds) == palette[4]


@pytest.mark.parametrize(
    "steps",
    [
        10,
        True,
        "5,20,50,100",
        [1, 2, 3],
        [1, 2, 3, 4, 5],
        [0, 2, 3, 4],
        [-1, 2, 3, 4],
        [1, 2, 3, math.nan],
        [1, 2, 3, math.inf],
        [1, 3, 2, 4],
        [1, 2, 2, 4],
        [True, 2, 3, 4],
        [1, 2, "not-a-number", 4],
    ],
)
def test_resolve_steps_rejects_invalid_thresholds(steps):
    with pytest.raises(ValueError):
        resolve_steps(100, steps)


def test_all_themes_have_five_colors():
    for name, palette in THEMES.items():
        assert len(palette) == 5, name


def test_mono_and_dark_themes_are_registered():
    assert "mono" in THEMES
    assert "dark" in THEMES
