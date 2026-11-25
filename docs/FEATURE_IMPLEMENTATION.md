# Feature implementation notes

The document describes the two feature groups added to the `heatmap-customization`
branch and how each is implemented across the Python API, SVG renderer, CLI, and tests.

## Customizable intensity thresholds

Quilt uses a five-color palette. There are four color-change thresholds
between those five colors, so `steps` must contain exactly four values.

The supplied values are absolute intensity thresholds. They identify the
exact values at which the cell moves to the next palette color. The argument must be a sequence containing exactly four numeric thresholds.
Each threshold must be positive and finite, and the sequence must be strictly
increasing. Invalid values raise `ValueError`.
For example, `steps=[5, 20, 50, 100]` defines these five bands:

| Input value | Palette color |
| --- | --- |
| `x < 5` | First color |
| `5 <= x < 20` | Second color |
| `20 <= x < 50` | Third color |
| `50 <= x < 100` | Fourth color |
| `x >= 100` | Fifth color |

### Python API

```python
svg = render_svg(counts, steps=[5, 20, 50, 100])
```

### CLI

```bash
habit-heatmap input.csv -o heatmap.svg --value-col minutes --steps 5,20,50,100
```

The CLI accepts exactly four comma-separated thresholds. Malformed input and
non-positive, non-finite, or non-increasing values are rejected by argument
parsing, before the input CSV is processed.

### Automatic scaling

When `steps=None` (the default), Quilt preserves its original automatic
scaling. If the maximum value in the rendered date range is `x > 0`, the
four boundaries are:

```python
[0, x / 4, x / 2, 3 * x / 4]
```

This is equivalent to the original automatic mapping: zero and negative values
use the lightest color; positive values move through the four remaining
boundaries as they cross the quartile cutoffs. Values outside an explicit
`start` / `end` rendering window do not affect `x`.  
If the in-range maximum is not positive, the automatic scale renders every
cell with the lightest color.

### Implementation by file

- `src/habit_heatmap/colors.py`
  - `resolve_steps(max_value, steps=None)` returns four thresholds. With no
    custom sequence it calculates the original boundaries
    `0, x/4, x/2, 3x/4`; with a custom sequence it validates and returns them 
    unchanged.
  - `color_for_steps(value, thresholds, palette)` maps a value to the
    five-color palette using the four thresholds. It uses right-inclusive
    transitions: a value equal to a threshold moves to the next
    palette color.
  - `bucket_color(..., steps=None)` preserves the existing convenience API
    and adds optional four-value absolute thresholds.
- `src/habit_heatmap/render_svg.py`
  - `render_svg(..., steps=None)` exposes the four thresholds in the public
    renderer.
  - The renderer calculates the maximum from values inside the rendered date
    range, resolves the four boundaries once, and uses `color_for_steps`
    for each day cell.
  - The automatic all-non-positive case remains lightest when `steps` is
    omitted.
- `src/habit_heatmap/cli.py`
  - `parse_steps` parses four comma-separated values and validates their
    count, finiteness, positivity, and strict ordering.
  - `--steps` passes the resulting four-value tuple to `render_svg`.
- **Tests**
  - `tests/test_colors.py` checks automatic boundaries, all four exact
    threshold transitions, values between and above thresholds, and invalid
    sequences.
  - `tests/test_render_svg.py` checks the actual SVG cell fill below, at, and
    above each supplied threshold, plus unchanged automatic scaling.
  - `tests/test_cli.py` checks CLI threshold application and rejects malformed
    or invalid threshold arguments.

## 2. Independent SVG text styling

Four SVG text features can be styled independently:
- Month labels
- Weekday labels
- Heatmap title (if supplied)
- Legend text (`Less` / `More`)

Each group has its own font-size and color argument. This allows a caller to
change one text group without changing the others.  
Font sizes must be positive finite numbers. Explicit colors must be 3- or
6-digit hexadecimal strings. When a color is omitted, Quilt chooses a readable
default from the selected theme's background: `#767676` for light backgrounds
and `#FFFFFF` for dark backgrounds. An explicit color overrides the default
only for its own text group.

### Python API

```python
svg = render_svg(
    counts,
    label="Activity",
    month_label_font_size=11,
    month_label_color="#767676",
    weekday_label_font_size=10,
    weekday_label_color="#767676",
    title_font_size=16,
    title_color="#24292f",
    legend_font_size=9,
    legend_color="#767676",
)
```

The defaults are 9 SVG units for month labels, weekday labels, and legend text,
and 14 for the title. Text colors default from the theme.

### CLI

The renderer options are exposed with hyphenated CLI flags:

- `--month-label-font-size` / `--month-label-color`
- `--weekday-label-font-size` / `--weekday-label-color`
- `--title-font-size` / `--title-color`
- `--legend-font-size` / `--legend-color`

For example:

```bash
habit-heatmap input.csv -o heatmap.svg \
  --label "Activity" \
  --title-font-size 16 --title-color "#24292f" \
  --legend-font-size 10 --legend-color "#767676"
```

### Implementation by file

- `src/habit_heatmap/render_svg.py`
  - `_label_style` validates a text group's font size and color and produces
    the SVG style attributes. It supports an optional font weight for the title.
  - `_default_label_color` derives the default text color from the background
    color of the selected theme.
  - `_weekday_labels`, `_month_labels`, and `_legend` accept a style string
    so their text can be configured independently.
  - `render_svg` exposes the eight public styling arguments and builds a
    separate style for each text group. The title is styled only when a label
    is supplied.
- `src/habit_heatmap/cli.py`
  - Defines the eight corresponding command-line options and forwards their
    values to `render_svg`.
- Tests
  - `tests/test_render_svg.py` checks independent styling, theme-derived
    defaults, explicit overrides, and invalid font sizes/colors.
  - `tests/test_cli.py` checks that the CLI forwards each style option and
    that the resulting SVG contains the expected text attributes.