# Backlog

Epic/story breakdown for the build phase. High-level by design — these guide
later build runs, not a detailed spec. Check off `[x]` as stories land.

## Epic 1: Rendering polish

Make the heatmap itself look and read like the reference it's imitating.

- [x] Add month labels above the grid and weekday labels (Mon/Wed/Fri) beside it
- [x] Add a color legend ("Less ... More") below the grid
- [x] Support a `--label` / title option rendered above the chart
- [x] Add at least two more themes (e.g. a monochrome/grayscale and a
      dark-background variant) and document how to add a custom one

## Epic 2: Parser flexibility

Widen what counts as "a CSV with a date column" so more real-world exports
work without preprocessing.

- [x] Support ISO 8601 datetimes (not just bare dates) by truncating to day
- [x] Add a `--tz` option to normalize timestamps to a given timezone before
      bucketing into days
- [x] Support reading from stdin (`-` as the CSV path) for pipeline use
- [x] Add a `load_events_from_rows()` variant that takes an iterable of dicts
      directly, for callers who already have parsed data (e.g. a DB query)
      instead of a CSV file

## Epic 3: CLI and packaging

Round out the command-line experience and get the package installable from
PyPI.

- [ ] Add `--week-start` to support Monday-start grids (ISO week convention)
- [ ] Add a `--quiet` flag and make the "wrote <path>" message opt-in via
      `--verbose` instead of unconditional
- [ ] Publish the package to PyPI and add install/version badges to the README
- [ ] Add a `habit-heatmap --version` flag

## Epic 4: Distribution and examples

Make it easy for someone to see themselves using this tool.

- [ ] Add a small gallery to `docs/` showing each theme rendered against the
      same example dataset
- [ ] Add a second example dataset in a different domain (e.g. mood ratings
      1-5) to show the value-column path isn't just for workout minutes
- [ ] Write a "cookbook" doc showing common recipes: git commit history,
      a habit-tracking app's CSV export, a spreadsheet time log
