# Habit Heatmap

[![CI](https://github.com/ctkrug/habit-heatmap/actions/workflows/ci.yml/badge.svg)](https://github.com/ctkrug/habit-heatmap/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Generate a GitHub-style contribution heatmap (SVG or PNG) from **any** CSV of dated
events — habit trackers, workout logs, git history exports, sleep data, whatever has a
date column.

```
python -m habit_heatmap workouts.csv -o heatmap.svg
```

![example heatmap](docs/example.svg)

## Why

GitHub's contribution graph is a great shape for "did I do the thing" data, but it's
locked to commits. Habit Heatmap takes the same visual language and points it at any
CSV: meditation streaks, reading logs, gym check-ins, mood ratings — anything with a
date and (optionally) a value.

## Features

- **Any CSV in.** Point it at a date column and (optionally) a numeric value column;
  rows are aggregated per day automatically.
- **SVG by default, PNG on request.** SVG output is dependency-free; PNG rasterization
  is an opt-in extra.
- **Themeable.** Ships with GitHub-green plus four alternate palettes (`blue`, `purple`,
  `mono`, `dark`); themes are just a 5-color tuple, easy to extend.
- **Labeled grid.** Month labels above, Mon/Wed/Fri weekday labels beside, and a
  "Less ... More" legend below — reads like the reference it's imitating.
- **Library or CLI.** Use `habit_heatmap.load_events` / `render_svg` directly from
  Python, or drive it from the command line.
- **No server, no accounts.** A single Python process reads a CSV and writes an image.

## Install

```
pip install habit-heatmap
```

For PNG export:

```
pip install "habit-heatmap[png]"
```

## Usage

```
habit-heatmap events.csv -o heatmap.svg \
  --date-col date \
  --value-col minutes \
  --theme blue \
  --label "Workouts"
```

As a library:

```python
from habit_heatmap import load_events, render_svg

counts = load_events("events.csv", value_col="minutes")
svg = render_svg(counts, theme="blue", label="Workouts")
```

### Themes

Built in: `github`, `blue`, `purple`, `mono` (grayscale), `dark` (for embedding on a
dark-mode page). To add your own, register a 5-color tuple — lightest (no activity)
to darkest (busiest) — in `habit_heatmap.colors.THEMES`:

```python
from habit_heatmap.colors import THEMES

THEMES["sunset"] = ("#fff5eb", "#fdbe85", "#fd8d3c", "#e6550d", "#a63603")
```

Then pass `theme="sunset"` to `render_svg` or `--theme sunset` on the CLI.

See [`docs/VISION.md`](docs/VISION.md) for the design rationale and
[`docs/BACKLOG.md`](docs/BACKLOG.md) for the planned roadmap.

## Stack

Pure-Python (stdlib CSV/argparse for the core), with `cairosvg` as an optional
dependency for PNG export. No runtime dependencies for the SVG path.

## License

MIT — see [`LICENSE`](LICENSE).
