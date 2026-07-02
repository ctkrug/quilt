import sys

import pytest

from habit_heatmap.render_png import svg_to_png

SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
    '<rect width="10" height="10"/></svg>'
)


def test_svg_to_png_writes_a_png_file(tmp_path):
    pytest.importorskip("cairosvg")
    output = tmp_path / "out.png"
    svg_to_png(SVG, str(output))
    assert output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_svg_to_png_reports_the_png_extra_when_cairosvg_is_missing(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "cairosvg", None)
    with pytest.raises(RuntimeError, match=r"habit-heatmap\[png\]"):
        svg_to_png(SVG, str(tmp_path / "out.png"))
