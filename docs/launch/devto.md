---
title: "I built Quilt: turn any CSV into a GitHub-style contribution heatmap"
published: false
tags: python, cli, dataviz, opensource
---

I have a spreadsheet where I log workouts. I also have the nagging feeling that the
single most motivating chart I look at all week is the one I did not make: GitHub's
contribution graph. That little grid of green squares is a great picture of "did I
show up," and it is stuck drawing one thing, my commits.

So I built [Quilt](https://github.com/ctkrug/habit-heatmap), a small Python tool that
draws the same grid from any CSV with a date column. One command turns my workout log
into the exact year-at-a-glance view I wanted:

```
habit-heatmap workouts.csv -o heatmap.svg --value-col minutes --label "Workouts"
```

It counts one square per row by default, or sums a numeric column per day when you pass
`--value-col`. That is the whole pitch. Here are the two decisions that shaped how it
turned out.

## One dict in the middle

The tool does two jobs: read a CSV into per-day totals, and draw those totals as a grid.
I made the seam between them a plain `dict[date, float]` and refused to let anything
fancier leak across it.

```python
counts = load_events("events.csv", value_col="minutes")  # {date: float}
svg = render_svg(counts, theme="blue", label="Workouts")  # str
```

That one boundary paid for itself three times. The parser and the renderer test
independently, because neither knows the other exists. The command line became a thin
wrapper instead of the place where all the logic hides. And anyone whose data is not in
a CSV can skip the parser completely: `load_events_from_rows` takes an iterable of
dictionaries, so a database cursor or an API response goes straight to a heatmap with no
temporary file.

```python
counts = load_events_from_rows(db.query("SELECT logged_at AS date, minutes FROM sets"))
```

I keep relearning this lesson. Picking the boring data structure in the middle and
guarding it is worth more than any clever function on either side.

## The color scale is relative, on purpose

GitHub's graph shades each day by how busy it was. The naive way to port that is to pick
fixed numeric cutoffs. The problem shows up the first time a light user runs it: if your
"a lot" is thirty minutes and the cutoffs assume hundreds, your whole year renders
pale gray and the chart tells you nothing.

With the default automatic scale, the darkest bucket is anchored to the busiest day in
the range you are actually rendering:

```python
in_range_values = [v for day, v in counts.items() if start <= day <= end]
max_value = max(in_range_values) if in_range_values else 0.0
```

The default relative scale is not mandatory. When I need comparable colors across
multiple heatmaps, I can supply four absolute color-change thresholds instead:

```python
svg = render_svg(counts, steps=[5, 20, 50, 100])
```

Those values are used exactly as written: the five palette colors apply to values
below 5, from 5 to below 20, from 20 to below 50, from 50 to below 100, and
100 or above. The four thresholds are not interval widths and are never added
together. Omitting `steps` keeps the automatic, range-relative scale.

The subtle part is `if start <= day <= end`. If you clip the window with `--start` and
`--end`, data outside that window must not influence the scale, or one busy month in
March could wash out the June you asked to see. This was a real bug I caught in QA: the
scale was being computed from the full dataset before the window was applied.

## What I would do differently

The month labels across the top were fiddlier than anything else. Short months sit close
together, so labels overlap, and the first column is usually padded with days from the
previous month. I ended up with a minimum-gap throttle and a special case for the leading
week. It works, but it is the one piece of code I would rewrite from a cleaner idea rather
than patch again.

## Try it

The core is pure Python with no runtime dependencies (PNG export is an opt-in extra). It
runs on 3.9 and up.

- Code: https://github.com/ctkrug/habit-heatmap
- More of my projects: https://apps.charliekrug.com

If you track anything in a spreadsheet, I would love to know what your grid looks like.
