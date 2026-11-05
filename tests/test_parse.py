from datetime import datetime

import pytest

from aire_abierto.parse import (
    iter_hourly_rows,
    parse_measurement,
    parse_timestamp,
    write_hourly_csv,
)
from aire_abierto.paths import sample_csv


def test_public_excerpt_keeps_flags_and_numbers():
    first = next(iter_hourly_rows(sample_csv()))
    assert first["station_code"] == "AGU"
    assert first["observed_at"] == "2025-05-01T00:00:00"
    assert float(first["o3_ppm"]) == pytest.approx(0.043)
    assert float(first["pm10_ugm3"]) == 46
    assert float(first["pm25_ugm3"]) == 12
    assert first["so2_ppm"] == ""
    assert first["so2_flag"] == "IO"
    assert first["co_flag"] == "ND"


def test_timestamps_and_flags():
    assert parse_timestamp("2025-01-01 00:00:00", 24) == datetime(2025, 1, 2, 0, 0)
    assert parse_timestamp("2025-01-01", 5) == datetime(2025, 1, 1, 5, 0)
    assert parse_timestamp("2024-01-01 13:00:00", 13) == datetime(2024, 1, 1, 13, 0)
    assert parse_measurement("IO") == (None, "IO")
    assert parse_measurement("1,5") == (1.5, None)
    assert parse_measurement(None) == (None, None)


def test_2024_shaped_header_with_extra_columns(tmp_path):
    path = tmp_path / "shaped.csv"
    path.write_text(
        "STATION,DATE,HOUR,DIA,MES ,O3,PM10,PM2.5\n"
        "MIR,2024-01-01 07:00:00,7,1,1,0.040,80,30\n",
        encoding="utf-8",
    )
    out = tmp_path / "hourly.csv"
    assert write_hourly_csv(path, out) == 1
    row = next(iter_hourly_rows(path))
    assert row["station_code"] == "MIR"
    assert row["observed_at"] == "2024-01-01T07:00:00"
    assert float(row["pm25_ugm3"]) == 30


def test_missing_station_column_is_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("DATE,O3\n2025-01-01,0.01\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing columns"):
        list(iter_hourly_rows(path))
