from habit_heatmap.colors import THEMES, bucket_color


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


def test_all_themes_have_five_colors():
    for name, palette in THEMES.items():
        assert len(palette) == 5, name


def test_mono_and_dark_themes_are_registered():
    assert "mono" in THEMES
    assert "dark" in THEMES
