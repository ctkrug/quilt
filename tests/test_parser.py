import io
from datetime import date, datetime
from pathlib import Path

import pytest

from habit_heatmap.parser import load_events, load_events_from_rows

FIXTURE = Path(__file__).parent / "fixtures" / "sample.csv"


def test_load_events_counts_rows_by_default():
    counts = load_events(FIXTURE)
    assert counts[date(2024, 1, 2)] == 2  # two rows on this date
    assert counts[date(2024, 1, 1)] == 1


def test_load_events_sums_value_column():
    counts = load_events(FIXTURE, value_col="value")
    assert counts[date(2024, 1, 2)] == 3  # 1 + 2
    assert counts[date(2024, 1, 1)] == 3
    assert counts[date(2024, 1, 8)] == 0


def test_load_events_rejects_missing_date_column():
    with pytest.raises(ValueError):
        load_events(FIXTURE, date_col="not_a_column")


def test_load_events_rejects_unparseable_date(tmp_path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("date,value\nnot-a-date,1\n")
    with pytest.raises(ValueError):
        load_events(bad_csv)


def test_load_events_truncates_iso_datetimes_to_day(tmp_path):
    csv_path = tmp_path / "events.csv"
    csv_path.write_text(
        "date,value\n"
        "2024-01-02T08:15:00,1\n"
        "2024-01-02T22:45:00Z,2\n"
        "2024-01-03T00:00:00+05:00,3\n"
    )
    counts = load_events(csv_path, value_col="value")
    assert counts[date(2024, 1, 2)] == 3
    assert counts[date(2024, 1, 3)] == 3


def test_load_events_normalizes_timestamps_to_tz(tmp_path):
    csv_path = tmp_path / "events.csv"
    # Both timestamps are Jan 1 evening in America/Chicago (UTC-6) despite
    # crossing the UTC day boundary.
    csv_path.write_text(
        "date,value\n2024-01-01T23:30:00Z,1\n2024-01-02T02:00:00Z,1\n"
    )
    utc_counts = load_events(csv_path)
    assert utc_counts == {date(2024, 1, 1): 1.0, date(2024, 1, 2): 1.0}

    chicago_counts = load_events(csv_path, tz="America/Chicago")
    assert chicago_counts == {date(2024, 1, 1): 2.0}


def test_load_events_assumes_utc_for_naive_timestamps_with_tz(tmp_path):
    csv_path = tmp_path / "events.csv"
    csv_path.write_text("date,value\n2024-01-01T23:30:00,1\n")
    counts = load_events(csv_path, tz="America/Chicago")
    assert counts == {date(2024, 1, 1): 1.0}


def test_load_events_reads_from_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("date,value\n2024-01-01,1\n2024-01-01,2\n"))
    counts = load_events("-", value_col="value")
    assert counts == {date(2024, 1, 1): 3.0}


def test_load_events_from_rows_accepts_string_dates():
    rows = [{"date": "2024-01-01", "value": "2"}, {"date": "2024-01-01", "value": "3"}]
    counts = load_events_from_rows(rows, value_col="value")
    assert counts == {date(2024, 1, 1): 5.0}


def test_load_events_from_rows_accepts_date_and_datetime_objects():
    rows = [
        {"date": date(2024, 1, 1), "minutes": 10},
        {"date": datetime(2024, 1, 1, 20, 0, 0), "minutes": 5},
    ]
    counts = load_events_from_rows(rows, value_col="minutes")
    assert counts == {date(2024, 1, 1): 15.0}


def test_load_events_from_rows_skips_rows_without_a_date():
    rows = [{"date": "2024-01-01"}, {"date": None}, {"date": ""}]
    counts = load_events_from_rows(rows)
    assert counts == {date(2024, 1, 1): 1.0}
