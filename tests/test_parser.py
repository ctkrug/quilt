from datetime import date
from pathlib import Path

import pytest

from habit_heatmap.parser import load_events

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
