"""Minimal example of using habit_heatmap as a library.

Run from the repo root: python examples/quickstart.py
"""

from pathlib import Path

from habit_heatmap import load_events, render_svg

csv_path = Path(__file__).parent / "workouts.csv"
counts = load_events(csv_path, value_col="minutes")
svg = render_svg(counts, theme="blue")

output_path = Path(__file__).parent / "quickstart.svg"
output_path.write_text(svg, encoding="utf-8")
print(f"wrote {output_path}")
