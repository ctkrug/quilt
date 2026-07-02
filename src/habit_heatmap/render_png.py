"""Optional PNG export of a rendered SVG heatmap (requires the 'png' extra)."""

from __future__ import annotations


def svg_to_png(svg: str, output_path: str) -> None:
    """Rasterize an SVG string to a PNG file using cairosvg."""
    try:
        import cairosvg
    except ImportError as exc:
        raise RuntimeError(
            "PNG export requires the 'png' extra: pip install 'habit-heatmap[png]'"
        ) from exc
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=output_path)
