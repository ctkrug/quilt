# Architecture

A concise map of the codebase for anyone picking this up cold. See
[`VISION.md`](VISION.md) for *why* it's built this way and
[`BACKLOG.md`](BACKLOG.md) for what's left.

## Layout

```
src/habit_heatmap/
  parser.py       # CSV/rows -> {date: float} aggregation
  colors.py       # theme palettes + value->bucket mapping
  render_svg.py   # {date: float} -> SVG string
  render_png.py   # optional SVG -> PNG rasterization (cairosvg extra)
  cli.py          # argparse wrapper around the two functions above
  __main__.py     # `python -m habit_heatmap` entrypoint -> cli.main
  version.py      # __version__, read by cli.py's --version and pyproject
tests/
  test_parser.py, test_colors.py, test_render_svg.py, test_render_png.py, test_cli.py
  fixtures/sample.csv
examples/
  quickstart.py, workouts.csv
docs/
  VISION.md, BACKLOG.md, ARCHITECTURE.md (this file), example.svg
```

## Data flow

```
CSV file / stdin / iterable of dicts
        │
        ▼
  parser.load_events() / load_events_from_rows()   -> dict[date, float]
        │
        ▼
  render_svg.render_svg()                          -> SVG string
        │
        ▼ (only if -o ends in .png)
  render_png.svg_to_png()                           -> PNG file
```

The `dict[date, float]` in the middle is the deliberate seam: `parser` and
`render_svg` are tested independently, and a caller with its own data
source (a DB query, an API) can skip `parser` entirely and call
`render_svg` directly, or use `load_events_from_rows` to skip file I/O
while keeping the standard date/value coercion rules.

## `parser.py`

- `_parse_datetime(raw, fmt)` — tries `fmt` (or `DEFAULT_DATE_FORMATS`:
  `%Y-%m-%d`, `%Y/%m/%d`, `%m/%d/%Y`) via `strptime`, then falls back to
  `datetime.fromisoformat` (after normalizing a trailing `Z`) for ISO 8601
  timestamps. Raises `ValueError` if nothing matches.
- `_to_moment(raw_date, fmt)` — same, but passes through values that are
  already `date`/`datetime` objects (the `load_events_from_rows` path).
- `_row_bucket(row, date_col, value_col, date_format, target_zone)` — the
  shared per-row logic: resolve the moment, apply timezone normalization
  (naive timestamps are assumed UTC) if `target_zone` is set, resolve the
  amount (row count of 1, or the summed `value_col`), and return
  `(date, amount)` or `None` to skip the row.
- `load_events(csv_path, ...)` — opens `csv_path` (or reads `sys.stdin` if
  `csv_path == "-"`, via `contextlib.nullcontext` so the stream isn't
  closed; file opens use `utf-8-sig` so an Excel-exported UTF-8 BOM doesn't
  glue itself onto the first header name), validates `date_col` is a real
  header, and folds every row through `_row_bucket` into a
  `defaultdict(float)`.
- `load_events_from_rows(rows, ...)` — same aggregation over any
  `Iterable[Mapping[str, Any]]`, no file I/O.
- A blank *or whitespace-only* date/value cell is treated as missing/zero
  rather than reaching `strptime`/`float()` with an empty string; a date
  value that's neither a `str` nor a `date`/`datetime` (e.g. a raw int from
  a DB row) raises a `ValueError` naming the bad type instead of an
  `AttributeError` from deep inside `_parse_datetime`.

## `colors.py`

- `THEMES: dict[str, tuple[str, ...]]` — each theme is a 5-color tuple,
  lightest (no activity) to darkest (busiest). Built in: `github`, `blue`,
  `purple`, `mono`, `dark`. Extending is just adding a key — see the
  README's "Themes" section.
- `bucket_color(value, max_value, palette)` — maps a value into one of the
  palette's 5 buckets, relative to `max_value` (so the busiest day in the
  rendered range is always the darkest cell, regardless of absolute scale).
  `value <= 0` (or `max_value <= 0`) always maps to the lightest bucket.

## `render_svg.py`

`render_svg(counts, ...)` composes a handful of independent element
builders into one `<svg>`. `theme` and `week_start` are validated against
`THEMES`/`WEEK_START_WEEKDAYS` and raise `ValueError` on an unknown value —
no silent fallback. The color scale's `max_value` is computed only from
`counts` entries that fall within `[start, end]`, so data outside an
explicit render window can't wash out (or exaggerate) the in-range scale.

- the day grid itself (one `<rect>` per day in `[start, end]`, positioned
  by `(week_index, weekday)` — `weekday` is `(date.weekday() - start_weekday) % 7`,
  which is what makes `week_start="monday"` a one-line generalization of
  the Sunday-only original math)
- `_weekday_labels` — Mon/Wed/Fri beside the grid, row position derived
  the same way
- `_month_labels` — one label per week column where the month changes,
  clamped so the leading (possibly padded) week uses `start`'s month, and
  throttled by `MONTH_LABEL_MIN_GAP_WEEKS` to avoid overlapping text
- `_legend` — the "Less ... More" strip, reusing the theme's own palette
- an optional `label` title, XML-escaped since it's arbitrary user input

Layout is all additive offsets from a handful of module-level constants
(`MARGIN`, `WEEKDAY_LABEL_WIDTH`, `MONTH_LABEL_HEIGHT`, `TITLE_HEIGHT`,
`LEGEND_HEIGHT`, ...) — the grid's origin (`grid_x0`, `grid_y0`) shifts
down/right based on which optional elements (`label`, `legend`) are on,
and the overall `width`/`height` are computed from that same origin.

## `cli.py`

Thin `argparse` layer: parses flags, calls `load_events` then
`render_svg`, writes the result (SVG directly, or via `render_png` if
`-o` ends in `.png`; `-o -` writes SVG to stdout instead, mirroring `-`
for stdin on the CSV argument). Output is silent by default; `--verbose`
prints a `wrote <path>` confirmation to stderr (`--quiet` is the explicit,
mutually-exclusive spelling of the default). `--theme` is restricted to
`THEMES`' keys via argparse `choices`. `main()` wraps the pipeline in a
single `try/except (ValueError, OSError, RuntimeError, LookupError)` so
expected failures (bad CSV data, unknown `--tz`, missing `cairosvg`) print
a one-line `habit-heatmap: error: ...` and exit 1 instead of a traceback.

## Running it

```
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q     # tests
ruff check src tests    # lint
python -m habit_heatmap examples/workouts.csv -o /tmp/heatmap.svg --verbose
```
