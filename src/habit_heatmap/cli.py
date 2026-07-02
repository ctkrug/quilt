"""Command-line interface for habit-heatmap."""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

from .colors import THEMES
from .parser import load_events
from .render_svg import render_svg
from .version import __version__


def _parse_iso_date(raw: str) -> date:
    return datetime.strptime(raw, "%Y-%m-%d").date()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="habit-heatmap",
        description="Generate a GitHub-style contribution heatmap from a CSV of dated events.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument("csv", help="path to the input CSV file, or - to read from stdin")
    parser.add_argument("-o", "--output", required=True, help="output file path (.svg or .png)")
    parser.add_argument("--date-col", default="date", help="date column name (default: date)")
    parser.add_argument(
        "--value-col", default=None, help="numeric column to sum per day (default: count rows)"
    )
    parser.add_argument("--date-format", default=None, help="explicit strptime format for dates")
    parser.add_argument(
        "--tz",
        default=None,
        help="IANA zone (e.g. America/Chicago) to normalize timestamps to before bucketing",
    )
    parser.add_argument(
        "--start", type=_parse_iso_date, default=None, help="first day to render (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end", type=_parse_iso_date, default=None, help="last day to render (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--theme",
        default="github",
        choices=sorted(THEMES),
        help="color theme (default: github)",
    )
    parser.add_argument("--label", default=None, help="title rendered above the chart")
    parser.add_argument(
        "--week-start",
        default="sunday",
        choices=("sunday", "monday"),
        help="first weekday of each grid column (default: sunday)",
    )
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "--verbose", action="store_true", help='print the "wrote <path>" message (default: off)'
    )
    verbosity.add_argument(
        "--quiet", action="store_true", help="suppress all output (the default; kept for clarity)"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        counts = load_events(
            args.csv,
            date_col=args.date_col,
            value_col=args.value_col,
            date_format=args.date_format,
            tz=args.tz,
        )
        svg = render_svg(
            counts,
            start=args.start,
            end=args.end,
            theme=args.theme,
            label=args.label,
            week_start=args.week_start,
        )

        output = Path(args.output)
        if output.suffix.lower() == ".png":
            from .render_png import svg_to_png

            svg_to_png(svg, str(output))
        else:
            output.write_text(svg, encoding="utf-8")
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"habit-heatmap: error: {exc}", file=sys.stderr)
        return 1

    if args.verbose:
        print(f"wrote {output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
