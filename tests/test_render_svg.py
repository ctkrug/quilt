import re
from datetime import date

import pytest

from habit_heatmap.render_svg import render_svg


def _rect_y(svg: str, day: str) -> int:
    match = re.search(rf'<rect x="\d+" y="(\d+)"[^>]*><title>{day}:', svg)
    assert match, f"no rect found for {day}"
    return int(match.group(1))


def test_render_svg_produces_one_rect_per_day():
    counts = {date(2024, 1, 1): 1, date(2024, 1, 3): 5}
    svg = render_svg(counts, start=date(2024, 1, 1), end=date(2024, 1, 3), legend=False)
    assert svg.count("<rect") == 3  # Jan 1, 2, 3 — including the empty middle day
    assert svg.startswith("<svg")


def test_render_svg_defaults_to_data_range():
    counts = {date(2024, 1, 1): 1, date(2024, 1, 10): 2}
    svg = render_svg(counts, legend=False)
    assert svg.count("<rect") == 10


def test_render_svg_darkest_cell_marks_the_max():
    counts = {date(2024, 1, 1): 1, date(2024, 1, 2): 10}
    svg = render_svg(counts, theme="github")
    assert 'fill="#216e39"' in svg  # darkest github green, for the day with value 10


def test_render_svg_requires_explicit_range_when_empty():
    with pytest.raises(ValueError):
        render_svg({})


def test_render_svg_rejects_inverted_range():
    with pytest.raises(ValueError):
        render_svg({date(2024, 1, 1): 1}, start=date(2024, 1, 5), end=date(2024, 1, 1))


def test_render_svg_includes_weekday_labels():
    counts = {date(2024, 1, 1): 1}
    svg = render_svg(counts)
    assert ">Mon<" in svg
    assert ">Wed<" in svg
    assert ">Fri<" in svg
    assert ">Sun<" not in svg


def test_render_svg_labels_the_start_month_not_the_padding_days():
    # Jan 1 2024 is a Monday, so the grid's leading week is padded with the
    # last Sunday of December; the label should still say Jan, not Dec.
    counts = {date(2024, 1, 1): 1}
    svg = render_svg(counts)
    assert ">Jan<" in svg
    assert ">Dec<" not in svg


def test_render_svg_labels_each_month_spanned():
    counts = {date(2024, 1, 1): 1, date(2024, 6, 15): 3, date(2024, 12, 31): 5}
    svg = render_svg(counts)
    for month in ("Jan", "Jun", "Dec"):
        assert f">{month}<" in svg


def test_render_svg_customizes_month_and_weekday_label_styles_independently():
    counts = {date(2024, 1, 1): 1, date(2024, 6, 1): 3}
    svg = render_svg(
        counts,
        month_label_font_size=14,
        month_label_color="#aabbcc",
        weekday_label_font_size=12,
        weekday_label_color="#112233",
    )
    assert 'font-size="14" fill="#aabbcc"' in svg
    assert 'font-size="12" fill="#112233"' in svg


@pytest.mark.parametrize("kwargs", [
    {"month_label_font_size": 0},
    {"month_label_font_size": -1},
    {"weekday_label_font_size": float("inf")},
    {"month_label_color": "red"},
    {"weekday_label_color": "#12345"},
    {"title_font_size": 0},
    {"legend_font_size": -1},
    {"title_color": "red"},
    {"legend_color": "#12345"},
])
def test_render_svg_rejects_invalid_label_styles(kwargs):
    with pytest.raises(ValueError):
        render_svg({date(2024, 1, 1): 1}, **kwargs)


@pytest.mark.parametrize("theme, expected", [
    ("github", "#767676"),
    ("blue", "#767676"),
    ("purple", "#767676"),
    ("mono", "#767676"),
    ("dark", "#FFFFFF"),
])
def test_render_svg_chooses_label_color_from_theme(theme, expected):
    svg = render_svg({date(2024, 1, 1): 1}, theme=theme)
    assert f'font-size="9" fill="{expected}"' in svg


def test_render_svg_explicit_label_colors_override_theme_defaults():
    svg = render_svg(
        {date(2024, 1, 1): 1},
        theme="dark",
        month_label_color="#aabbcc",
        weekday_label_color="#112233",
    )
    assert 'font-size="9" fill="#aabbcc"' in svg
    assert 'font-size="9" fill="#112233"' in svg


@pytest.mark.parametrize("theme, expected", [
    ("github", "#767676"),
    ("blue", "#767676"),
    ("purple", "#767676"),
    ("mono", "#767676"),
    ("dark", "#FFFFFF"),
])
def test_render_svg_chooses_title_and_legend_colors_from_theme(theme, expected):
    svg = render_svg({date(2024, 1, 1): 1}, theme=theme, label="Run")
    assert f'font-size="14" font-weight="600" fill="{expected}">Run</text>' in svg
    assert f'font-size="9" fill="{expected}">Less</text>' in svg
    assert f'font-size="9" fill="{expected}">More</text>' in svg


def test_render_svg_customizes_title_and_legend_styles_independently():
    svg = render_svg(
        {date(2024, 1, 1): 1},
        theme="dark",
        label="Run",
        title_font_size=16,
        title_color="#aabbcc",
        legend_font_size=11,
        legend_color="#112233",
    )
    assert 'font-size="16" font-weight="600" fill="#aabbcc">Run</text>' in svg
    assert 'font-size="11" fill="#112233">Less</text>' in svg
    assert 'font-size="11" fill="#112233">More</text>' in svg


def test_render_svg_keeps_title_and_legend_colors_independent():
    svg = render_svg(
        {date(2024, 1, 1): 1},
        theme="dark",
        label="Run",
        title_color="#aabbcc",
    )
    assert 'font-size="14" font-weight="600" fill="#aabbcc">Run</text>' in svg
    assert 'font-size="9" fill="#FFFFFF">Less</text>' in svg


def test_render_svg_allows_independent_automatic_and_custom_label_colors():
    svg = render_svg(
        {date(2024, 1, 1): 1},
        theme="dark",
        month_label_color="#aabbcc",
    )
    assert 'font-size="9" fill="#aabbcc"' in svg
    assert 'font-size="9" fill="#FFFFFF"' in svg


def test_render_svg_includes_legend_by_default():
    counts = {date(2024, 1, 1): 1}
    svg = render_svg(counts)
    assert ">Less<" in svg
    assert ">More<" in svg


def test_render_svg_legend_can_be_disabled():
    counts = {date(2024, 1, 1): 1}
    svg = render_svg(counts, legend=False)
    assert ">Less<" not in svg
    assert ">More<" not in svg


def test_render_svg_omits_title_by_default():
    counts = {date(2024, 1, 1): 1}
    svg = render_svg(counts)
    assert "<text" in svg  # weekday/month/legend labels still present
    assert "font-weight" not in svg  # only the title uses bold text


def test_render_svg_renders_and_escapes_title():
    counts = {date(2024, 1, 1): 1}
    svg = render_svg(counts, label="Reading <streak> & more")
    assert "Reading &lt;streak&gt; &amp; more" in svg
    assert "<streak>" not in svg


def test_render_svg_week_start_defaults_to_sunday():
    counts = {date(2024, 1, 1): 1}
    default_svg = render_svg(counts, legend=False)
    explicit_svg = render_svg(counts, legend=False, week_start="sunday")
    assert _rect_y(default_svg, "2024-01-01") == _rect_y(explicit_svg, "2024-01-01")


def test_render_svg_week_start_monday_moves_monday_to_the_top_row():
    counts = {date(2024, 1, 1): 1}  # a Monday
    sunday_start = render_svg(counts, legend=False, week_start="sunday")
    monday_start = render_svg(counts, legend=False, week_start="monday")
    assert _rect_y(monday_start, "2024-01-01") < _rect_y(sunday_start, "2024-01-01")


def test_render_svg_rejects_unknown_week_start():
    with pytest.raises(ValueError):
        render_svg({date(2024, 1, 1): 1}, week_start="tuesday")


def test_render_svg_treats_all_negative_values_as_lightest():
    # e.g. a "weight change" dataset where every day is a loss.
    counts = {date(2024, 1, 1): -3, date(2024, 1, 2): -1}
    svg = render_svg(counts, legend=False)
    cell_colors = set(re.findall(r'<rect[^>]*fill="(#[0-9a-f]+)"', svg))
    assert cell_colors == {"#ebedf0"}  # github's lightest/no-activity shade


def test_render_svg_rejects_unknown_theme():
    with pytest.raises(ValueError):
        render_svg({date(2024, 1, 1): 1}, theme="neon")


def test_render_svg_color_scale_ignores_values_outside_the_range():
    # A huge value far outside an explicit render window shouldn't wash out
    # the scale for the day that's actually the busiest *within* the window.
    counts = {date(2024, 1, 1): 1, date(2024, 6, 1): 100}
    svg = render_svg(counts, start=date(2024, 1, 1), end=date(2024, 1, 7), legend=False)
    assert 'fill="#216e39"' in svg  # darkest github green, for Jan 1 within the window


def _rect_fill(svg: str, day: str) -> str:
    match = re.search(rf'<rect[^>]*fill="(#[0-9a-f]+)"><title>{day}:', svg)
    assert match, f"no rect found for {day}"
    return match.group(1)


def test_render_svg_uses_four_exact_color_change_thresholds():
    counts = {
        date(2024, 1, 1): -1,
        date(2024, 1, 2): 0,
        date(2024, 1, 3): 4,
        date(2024, 1, 4): 5,
        date(2024, 1, 5): 19,
        date(2024, 1, 6): 20,
        date(2024, 1, 7): 49,
        date(2024, 1, 8): 50,
        date(2024, 1, 9): 99,
        date(2024, 1, 10): 100,
        date(2024, 1, 11): 150,
    }
    svg = render_svg(counts, steps=[5, 20, 50, 100], legend=False)

    assert _rect_fill(svg, "2024-01-01") == "#ebedf0"
    assert _rect_fill(svg, "2024-01-02") == "#ebedf0"
    assert _rect_fill(svg, "2024-01-03") == "#ebedf0"
    assert _rect_fill(svg, "2024-01-04") == "#9be9a8"
    assert _rect_fill(svg, "2024-01-05") == "#9be9a8"
    assert _rect_fill(svg, "2024-01-06") == "#40c463"
    assert _rect_fill(svg, "2024-01-07") == "#40c463"
    assert _rect_fill(svg, "2024-01-08") == "#30a14e"
    assert _rect_fill(svg, "2024-01-09") == "#30a14e"
    assert _rect_fill(svg, "2024-01-10") == "#216e39"
    assert _rect_fill(svg, "2024-01-11") == "#216e39"


def test_render_svg_default_scaling_retains_existing_boundaries():
    counts = {
        date(2024, 1, 1): 1,
        date(2024, 1, 2): 25,
        date(2024, 1, 3): 50,
        date(2024, 1, 4): 75,
        date(2024, 1, 5): 100,
    }
    svg = render_svg(counts, legend=False)
    assert _rect_fill(svg, "2024-01-01") == "#9be9a8"
    assert _rect_fill(svg, "2024-01-02") == "#40c463"
    assert _rect_fill(svg, "2024-01-03") == "#30a14e"
    assert _rect_fill(svg, "2024-01-04") == "#216e39"
    assert _rect_fill(svg, "2024-01-05") == "#216e39"


@pytest.mark.parametrize(
    "steps",
    [
        10,
        [1, 2, 3],
        [1, 2, 3, 4, 5],
        [0, 2, 3, 4],
        [-1, 2, 3, 4],
        [1, 2, 2, 4],
        [1, 3, 2, 4],
        [1, 2, 3, float("nan")],
        [1, 2, 3, float("inf")],
    ],
)
def test_render_svg_rejects_invalid_steps(steps):
    with pytest.raises(ValueError):
        render_svg({date(2024, 1, 1): 1}, steps=steps, legend=False)
