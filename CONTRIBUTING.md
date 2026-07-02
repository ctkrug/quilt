# Contributing

## Setup

```
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running checks locally

```
pytest
ruff check .
```

Both run in CI on every push and pull request; please make sure they pass
before opening a PR.

## Project layout

- `src/habit_heatmap/parser.py` — CSV parsing and per-day aggregation
- `src/habit_heatmap/render_svg.py` — grid layout and SVG generation
- `src/habit_heatmap/render_png.py` — optional PNG export
- `src/habit_heatmap/cli.py` — command-line interface
- `tests/` — unit tests for each of the above

See [`docs/VISION.md`](docs/VISION.md) for the design rationale and
[`docs/BACKLOG.md`](docs/BACKLOG.md) for planned work.
