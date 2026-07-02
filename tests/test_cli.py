import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "sample.csv"


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
