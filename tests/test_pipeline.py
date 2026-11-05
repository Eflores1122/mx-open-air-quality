from datetime import date

from aire_abierto.ingest import IngestError, acquire
from aire_abierto.parse import write_hourly_csv
from aire_abierto.paths import repo_root
from aire_abierto.pipeline import run_pipeline
from aire_abierto.quality import assess
from aire_abierto.transform import open_warehouse


def test_sample_excerpt_builds_metrics_and_passes_quality(tmp_path):
    result = run_pipeline(
        source="sample",
        year=2025,
        out_dir=tmp_path,
        as_of=date(2026, 11, 5),
    )
    assert result["ok"] is True
    assert result["manifest"]["data_kind"] == "official_excerpt"
    assert result["manifest"]["not_official_index"] is True
    quality = {item["id"]: item for item in result["quality"]["checks"]}
    assert quality["duplicate_keys"]["status"] == "pass"
    assert quality["freshness"]["status"] == "warn"
    assert quality["row_count"]["metrics"]["stations"] == 13
    assert (tmp_path / "daily_station.csv").is_file()
    assert (tmp_path / "daily_metro.csv").is_file()
    assert (tmp_path / "station_rank.csv").is_file()


def test_synthetic_fallback_is_labeled_and_ranks_the_south_station(tmp_path):
    result = run_pipeline(source="synthetic", year=2025, out_dir=tmp_path, as_of=date(2026, 11, 5))
    assert result["ok"] is True
    assert result["manifest"]["data_kind"] == "synthetic"
    assert "invent" in result["manifest"]["note_es"].lower() or "inventados" in result["manifest"]["note_es"]
    rank = (tmp_path / "station_rank.csv").read_text(encoding="utf-8").splitlines()
    assert rank[1].startswith("SYN-SUR,")
    daily_rows = (tmp_path / "daily_station.csv").read_text(encoding="utf-8")
    # Midnight belongs to the previous civil day, so 1 May starts a full day
    # and the opening 00:00 is only a stub on 30 April.
    assert "2025-04-30" in daily_rows
    sur_may1 = [
        line
        for line in daily_rows.splitlines()
        if line.startswith("SYN-SUR,") and ",2025-05-01," in line
    ]
    assert sur_may1
    assert ",24," in sur_may1[0]
    daily = (tmp_path / "daily_station.csv").read_text(encoding="utf-8")
    assert "SYN-SUR" in daily
    assert ",mala," in daily


def test_auto_uses_the_excerpt_when_the_download_fails(tmp_path, monkeypatch):
    def _boom(**kwargs):
        raise IngestError("no network")

    monkeypatch.setattr("aire_abierto.ingest._live", _boom)
    acquired = acquire("auto", year=2025, root=repo_root(), work_dir=tmp_path)
    assert acquired.data_kind == "official_excerpt"
    assert acquired.fallback_reason == "no network"


def test_duplicate_hours_fail_the_quality_check(tmp_path):
    source = tmp_path / "dup.csv"
    source.write_text(
        "STATION,DATE,HOUR,O3,PM2.5\n"
        "CEN,2025-01-01 01:00:00,1,0.02,10\n"
        "CEN,2025-01-01 01:00:00,1,0.03,11\n",
        encoding="utf-8",
    )
    hourly = tmp_path / "hourly.csv"
    write_hourly_csv(source, hourly)
    connection = open_warehouse(hourly, tmp_path / "aire.duckdb")
    try:
        report = assess(connection, as_of=date(2026, 11, 5), data_kind="official_excerpt", year=None)
    finally:
        connection.close()
    assert report.ok is False
    failed = [check.id for check in report.checks if check.status == "fail"]
    assert "duplicate_keys" in failed


def test_impossible_units_fail_instead_of_being_converted(tmp_path):
    source = tmp_path / "ppb.csv"
    lines = ["STATION,DATE,HOUR,O3,PM2.5"]
    for hour in range(24):
        lines.append(f"CEN,2025-01-01 {hour:02d}:00:00,{hour},40,20")
    source.write_text("\n".join(lines) + "\n", encoding="utf-8")
    hourly = tmp_path / "hourly.csv"
    write_hourly_csv(source, hourly)
    connection = open_warehouse(hourly, tmp_path / "aire.duckdb")
    try:
        report = assess(connection, as_of=date(2026, 11, 5), data_kind="official_excerpt", year=None)
    finally:
        connection.close()
    units = next(check for check in report.checks if check.id == "unit_sanity")
    assert units.status == "fail"
    assert report.ok is False
