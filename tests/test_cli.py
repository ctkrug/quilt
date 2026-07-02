import subprocess
import sys
from pathlib import Path

import pytest

from habit_heatmap.version import __version__

FIXTURE = Path(__file__).parent / "fixtures" / "sample.csv"


def test_cli_prints_version(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "habit_heatmap", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert __version__ in result.stdout


def test_cli_writes_svg_file(tmp_path):
    output = tmp_path / "heatmap.svg"
    result = subprocess.run(
        [sys.executable, "-m", "habit_heatmap", str(FIXTURE), "-o", str(output)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert output.exists()
    assert output.read_text().startswith("<svg")


def test_cli_applies_label(tmp_path):
    output = tmp_path / "heatmap.svg"
    result = subprocess.run(
        [sys.executable, "-m", "habit_heatmap", str(FIXTURE), "-o", str(output), "--label", "Gym"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert ">Gym<" in output.read_text()


def test_cli_applies_tz(tmp_path):
    csv_path = tmp_path / "events.csv"
    # Both fall on Jan 1 in America/Chicago (UTC-6), so with --tz the whole
    # range collapses to a single day and thus a single grid cell.
    csv_path.write_text("date,value\n2024-01-01T23:30:00Z,1\n2024-01-02T02:00:00Z,1\n")
    output = tmp_path / "heatmap.svg"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "habit_heatmap",
            str(csv_path),
            "-o",
            str(output),
            "--tz",
            "America/Chicago",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    svg = output.read_text()
    assert svg.count("2024-01-01") == 1
    assert "2024-01-02" not in svg


def test_cli_reads_from_stdin(tmp_path):
    output = tmp_path / "heatmap.svg"
    result = subprocess.run(
        [sys.executable, "-m", "habit_heatmap", "-", "-o", str(output)],
        input=FIXTURE.read_text(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert output.read_text().startswith("<svg")


def test_cli_rejects_invalid_week_start(tmp_path):
    output = tmp_path / "heatmap.svg"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "habit_heatmap",
            str(FIXTURE),
            "-o",
            str(output),
            "--week-start",
            "tuesday",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert not output.exists()


def test_cli_is_silent_by_default(tmp_path):
    output = tmp_path / "heatmap.svg"
    result = subprocess.run(
        [sys.executable, "-m", "habit_heatmap", str(FIXTURE), "-o", str(output)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""


def test_cli_verbose_prints_wrote_message(tmp_path):
    output = tmp_path / "heatmap.svg"
    result = subprocess.run(
        [sys.executable, "-m", "habit_heatmap", str(FIXTURE), "-o", str(output), "--verbose"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert f"wrote {output}" in result.stderr


def test_cli_rejects_verbose_and_quiet_together(tmp_path):
    output = tmp_path / "heatmap.svg"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "habit_heatmap",
            str(FIXTURE),
            "-o",
            str(output),
            "--verbose",
            "--quiet",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_cli_applies_value_col(tmp_path):
    csv_path = tmp_path / "events.csv"
    csv_path.write_text("date,minutes\n2024-01-01,10\n2024-01-01,5\n")
    output = tmp_path / "heatmap.svg"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "habit_heatmap",
            str(csv_path),
            "-o",
            str(output),
            "--value-col",
            "minutes",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "2024-01-01: 15" in output.read_text()


def test_cli_applies_week_start_monday(tmp_path):
    csv_path = tmp_path / "events.csv"
    csv_path.write_text("date,value\n2024-01-01,1\n")  # a Monday
    sunday_output = tmp_path / "sunday.svg"
    monday_output = tmp_path / "monday.svg"
    for output, week_start in ((sunday_output, "sunday"), (monday_output, "monday")):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "habit_heatmap",
                str(csv_path),
                "-o",
                str(output),
                "--week-start",
                week_start,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
    assert sunday_output.read_text() != monday_output.read_text()


def test_cli_applies_date_format(tmp_path):
    csv_path = tmp_path / "events.csv"
    csv_path.write_text("logged_at,value\n01-Mar-2024,1\n")
    output = tmp_path / "heatmap.svg"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "habit_heatmap",
            str(csv_path),
            "-o",
            str(output),
            "--date-col",
            "logged_at",
            "--date-format",
            "%d-%b-%Y",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "2024-03-01" in output.read_text()


def test_cli_reports_missing_column(tmp_path):
    output = tmp_path / "heatmap.svg"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "habit_heatmap",
            str(FIXTURE),
            "-o",
            str(output),
            "--date-col",
            "not_a_column",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert not output.exists()


def test_cli_writes_png_file(tmp_path):
    pytest.importorskip("cairosvg")
    output = tmp_path / "heatmap.png"
    result = subprocess.run(
        [sys.executable, "-m", "habit_heatmap", str(FIXTURE), "-o", str(output)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_cli_writes_svg_to_stdout_when_output_is_dash(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "habit_heatmap", str(FIXTURE), "-o", "-"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("<svg")
    assert not (tmp_path / "-").exists()


def test_cli_renders_explicit_start_and_end_for_a_dateless_csv(tmp_path):
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("date,value\n")
    output = tmp_path / "heatmap.svg"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "habit_heatmap",
            str(empty_csv),
            "-o",
            str(output),
            "--start",
            "2024-01-01",
            "--end",
            "2024-01-07",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert output.read_text().count("<title>") == 7  # one day cell per date in range


def test_cli_rejects_invalid_theme(tmp_path):
    output = tmp_path / "heatmap.svg"
    result = subprocess.run(
        [sys.executable, "-m", "habit_heatmap", str(FIXTURE), "-o", str(output), "--theme", "neon"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert not output.exists()
    assert "invalid choice" in result.stderr


def test_cli_reports_unparseable_date_without_a_traceback(tmp_path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("date,value\nnot-a-date,1\n")
    output = tmp_path / "heatmap.svg"
    result = subprocess.run(
        [sys.executable, "-m", "habit_heatmap", str(bad_csv), "-o", str(output)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert not output.exists()
    assert "Traceback" not in result.stderr
    assert "habit-heatmap: error:" in result.stderr


def test_cli_reports_unknown_timezone_without_a_traceback(tmp_path):
    output = tmp_path / "heatmap.svg"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "habit_heatmap",
            str(FIXTURE),
            "-o",
            str(output),
            "--tz",
            "Not/AZone",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert not output.exists()
    assert "Traceback" not in result.stderr
    assert "habit-heatmap: error:" in result.stderr


def test_cli_reports_empty_range_without_a_traceback(tmp_path):
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("date,value\n")
    output = tmp_path / "heatmap.svg"
    result = subprocess.run(
        [sys.executable, "-m", "habit_heatmap", str(empty_csv), "-o", str(output)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert not output.exists()
    assert "Traceback" not in result.stderr
    assert "habit-heatmap: error:" in result.stderr
