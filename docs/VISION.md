# Vision

## The problem

GitHub's contribution graph is one of the most legible data visualizations in
day-to-day software life — a single glance tells you rhythm, streaks, and
gaps over a year. But it's locked to one dataset (commits) and one host
(GitHub). Anyone who wants that same "did I show up" view for a habit,
workout log, mood tracker, or anything else has to build it themselves.

## Who it's for

- People tracking a personal habit in a spreadsheet or CSV export (workouts,
  meditation, reading, sobriety, sleep) who want a visual streak view
  without adopting a whole habit-tracking app.
- Developers who want a drop-in heatmap for a dashboard, blog post, or
  README, and don't want to pull in a charting library for one chart shape.
- Anyone with dated tabular data (payments, support tickets, sensor
  readings) who wants a fast "when did things happen" overview.

## The core idea

**Any CSV with a date column becomes a heatmap.** The library does two
things and does them well:

1. `load_events` — read a CSV, aggregate rows per calendar day (count rows,
   or sum a numeric column), and hand back a plain `dict[date, float]`.
2. `render_svg` — take that dict and produce a GitHub-style week grid as a
   self-contained SVG string.

Everything else (CLI, themes, PNG export) is a thin layer on top of those
two functions. The dict-in-the-middle contract is deliberate: it's the
seam that keeps parsing and rendering independently testable and lets
someone plug in their own data source (a database query, an API call)
without touching the renderer.

## Key design decisions

- **Stdlib-only core.** The CSV parser and SVG renderer have zero runtime
  dependencies. Anything that pulls in a third-party package (PNG
  rasterization via `cairosvg`) is an opt-in extra, not a default install
  cost.
- **SVG as the primary output.** SVG is text, diffable, embeddable directly
  in Markdown/HTML, and infinitely scalable — better defaults for a tool
  whose main consumer is "paste this in a README or a web page" than a
  raster format.
- **Library first, CLI second.** `load_events`/`render_svg` are the public
  API; `cli.py` is a thin argparse wrapper around them. This keeps the CLI
  honest — if something is awkward to do as a library call, it's awkward
  in the CLI too, so there's pressure to fix the API instead of papering
  over it with flags.
- **Data decides the range by default.** Given no explicit `--start`/`--end`,
  the renderer spans exactly the dates present in the data. Explicit range
  overrides exist for "always show the last full year" use cases, but
  nothing is assumed by default.
- **Color scale is relative, not absolute.** The darkest cell always marks
  the busiest day *in the rendered range*, so a light user's chart is just
  as legible as a heavy user's — nobody's heatmap is all pale gray because
  their "a lot" is someone else's "a little."

## What "v1 done" looks like

- `pip install habit-heatmap` gives you a `habit-heatmap` CLI and an
  importable `habit_heatmap` package.
- Any CSV with a date column (and optionally a numeric value column) can be
  turned into an SVG heatmap in one command, with sensible defaults.
- PNG export works via an opt-in extra, for contexts that can't render SVG.
- At least three color themes ship out of the box, and adding a new one is
  a one-line addition to `colors.THEMES`.
- The test suite covers the parser's aggregation rules, the renderer's grid
  math and color bucketing, and the CLI's happy and failure paths.
- The library API is stable enough that someone could publish their own
  wrapper (a GitHub Action, a static-site generator plugin) against it
  without it changing underneath them.
