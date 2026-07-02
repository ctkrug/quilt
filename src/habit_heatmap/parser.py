"""Parse CSV files of dated events into a date -> total mapping."""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Optional, Union

DEFAULT_DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y")


def _parse_date(raw: str, fmt: Optional[str] = None) -> date:
    raw = raw.strip()
    formats = (fmt,) if fmt else DEFAULT_DATE_FORMATS
    for candidate in formats:
        try:
            return datetime.strptime(raw, candidate).date()
        except ValueError:
            continue
    raise ValueError(f"could not parse date {raw!r} with format(s) {formats}")


def load_events(
    csv_path: Union[str, Path],
    date_col: str = "date",
    value_col: Optional[str] = None,
    date_format: Optional[str] = None,
) -> dict[date, float]:
    """Aggregate a CSV of dated events into per-day totals.

    Rows with a missing or empty date are skipped. When ``value_col`` is
    omitted, each row contributes a count of 1 to its date's total;
    otherwise the numeric values in ``value_col`` are summed per day.
    """
    counts: dict[date, float] = defaultdict(float)
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if date_col not in (reader.fieldnames or []):
            raise ValueError(f"CSV has no {date_col!r} column; found {reader.fieldnames}")
        for row in reader:
            raw_date = row.get(date_col)
            if not raw_date:
                continue
            day = _parse_date(raw_date, date_format)
            amount = 1.0
            if value_col:
                raw_value = row.get(value_col)
                amount = float(raw_value) if raw_value else 0.0
            counts[day] += amount
    return dict(counts)
