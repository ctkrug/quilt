from datetime import date

import pytest

from habit_heatmap.render_svg import render_svg


def test_render_svg_produces_one_rect_per_day():
    counts = {date(2024, 1, 1): 1, date(2024, 1, 3): 5}
    svg = render_svg(counts, start=date(2024, 1, 1), end=date(2024, 1, 3))
    assert svg.count("<rect") == 3  # Jan 1, 2, 3 — including the empty middle day
    assert svg.startswith("<svg")


def test_render_svg_defaults_to_data_range():
    counts = {date(2024, 1, 1): 1, date(2024, 1, 10): 2}
    svg = render_svg(counts)
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
