"""Parse CSV files of dated events into a date -> total mapping."""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from collections.abc import Iterable, Mapping
from contextlib import nullcontext
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

DEFAULT_DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y")


def _parse_datetime(raw: str, fmt: str | None = None) -> datetime:
    raw = raw.strip()
    formats = (fmt,) if fmt else DEFAULT_DATE_FORMATS
    for candidate in formats:
        try:
            return datetime.strptime(raw, candidate)
        except ValueError:
            continue
    if fmt is None:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
    raise ValueError(f"could not parse date {raw!r} with format(s) {formats}")


def _to_moment(raw_date: Any, fmt: str | None) -> datetime:
    """Coerce a row's date value to a datetime, accepting already-parsed
    date/datetime objects (e.g. from a DB query) as well as strings."""
    if isinstance(raw_date, datetime):
        return raw_date
    if isinstance(raw_date, date):
        return datetime(raw_date.year, raw_date.month, raw_date.day)
    return _parse_datetime(raw_date, fmt)


def _row_bucket(
    row: Mapping[str, Any],
    date_col: str,
    value_col: str | None,
    date_format: str | None,
    target_zone: ZoneInfo | None,
) -> tuple[date, float] | None:
    """Extract the (day, amount) contribution of one row, or None to skip it."""
    raw_date = row.get(date_col)
    if not raw_date:
        return None
    moment = _to_moment(raw_date, date_format)
    if target_zone is not None:
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        moment = moment.astimezone(target_zone)
    amount = 1.0
    if value_col:
        raw_value = row.get(value_col)
        amount = float(raw_value) if raw_value else 0.0
    return moment.date(), amount


def load_events(
    csv_path: str | Path,
    date_col: str = "date",
    value_col: str | None = None,
    date_format: str | None = None,
    tz: str | None = None,
) -> dict[date, float]:
    """Aggregate a CSV of dated events into per-day totals.

    Rows with a missing or empty date are skipped. When ``value_col`` is
    omitted, each row contributes a count of 1 to its date's total;
    otherwise the numeric values in ``value_col`` are summed per day.

    When ``tz`` is given (an IANA zone name, e.g. ``"America/Chicago"``),
    each timestamp is normalized to that zone before bucketing into a day;
    a timestamp with no UTC offset of its own is assumed to be UTC.

    Pass ``"-"`` as ``csv_path`` to read the CSV from stdin instead of a file.
    """
    target_zone = ZoneInfo(tz) if tz else None
    counts: dict[date, float] = defaultdict(float)
    if csv_path == "-":
        source = nullcontext(sys.stdin)
    else:
        source = open(csv_path, newline="", encoding="utf-8")
    with source as fh:
        reader = csv.DictReader(fh)
        if date_col not in (reader.fieldnames or []):
            raise ValueError(f"CSV has no {date_col!r} column; found {reader.fieldnames}")
        for row in reader:
            bucket = _row_bucket(row, date_col, value_col, date_format, target_zone)
            if bucket is None:
                continue
            day, amount = bucket
            counts[day] += amount
    return dict(counts)


def load_events_from_rows(
    rows: Iterable[Mapping[str, Any]],
    date_col: str = "date",
    value_col: str | None = None,
    date_format: str | None = None,
    tz: str | None = None,
) -> dict[date, float]:
    """Aggregate an iterable of dict-like rows into per-day totals.

    Same aggregation rules as :func:`load_events`, for callers who already
    have parsed rows (e.g. a database query result) instead of a CSV file.
    Each row's date value may be a string (parsed the same way as a CSV
    cell) or an already-parsed ``date``/``datetime`` object.
    """
    target_zone = ZoneInfo(tz) if tz else None
    counts: dict[date, float] = defaultdict(float)
    for row in rows:
        bucket = _row_bucket(row, date_col, value_col, date_format, target_zone)
        if bucket is None:
            continue
        day, amount = bucket
        counts[day] += amount
    return dict(counts)
