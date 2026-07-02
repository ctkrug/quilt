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
