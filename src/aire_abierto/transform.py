"""Land hourly rows in DuckDB and aggregate them with SQL.

Python then applies the NOM-172 bands. The split keeps the window and
completeness math in SQL, where it is easier to audit, and keeps the
band-edge rule in one Python function with tests.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import duckdb

from aire_abierto.bands import MIN_VALID_HOURS, band_for, worst_band
from aire_abierto.stations import Station, display_name

CONCENTRATION_SQL = """
CREATE OR REPLACE TABLE hourly AS
SELECT
  station_code,
  CAST(observed_at AS TIMESTAMP) AS observed_at,
  TRY_CAST(NULLIF(o3_ppm, '') AS DOUBLE) AS o3_ppm,
  TRY_CAST(NULLIF(no2_ppm, '') AS DOUBLE) AS no2_ppm,
  TRY_CAST(NULLIF(so2_ppm, '') AS DOUBLE) AS so2_ppm,
  TRY_CAST(NULLIF(co_ppm, '') AS DOUBLE) AS co_ppm,
  TRY_CAST(NULLIF(pm10_ugm3, '') AS DOUBLE) AS pm10_ugm3,
  TRY_CAST(NULLIF(pm25_ugm3, '') AS DOUBLE) AS pm25_ugm3,
  NULLIF(o3_flag, '') AS o3_flag,
  NULLIF(no2_flag, '') AS no2_flag,
  NULLIF(so2_flag, '') AS so2_flag,
  NULLIF(co_flag, '') AS co_flag,
  NULLIF(pm10_flag, '') AS pm10_flag,
  NULLIF(pm25_flag, '') AS pm25_flag
FROM read_csv(?, header = true, all_varchar = true);

CREATE OR REPLACE TABLE co_windows AS
SELECT
  station_code,
  observed_at,
  CASE
    WHEN n_rows = 8 AND span_hours = 7 AND n_valid >= 6 THEN mean_co
    ELSE NULL
  END AS co_8h
FROM (
  SELECT
    station_code,
    observed_at,
    AVG(co_ppm) OVER w AS mean_co,
    COUNT(co_ppm) OVER w AS n_valid,
    COUNT(*) OVER w AS n_rows,
    date_diff('hour', MIN(observed_at) OVER w, observed_at) AS span_hours
  FROM hourly
  WINDOW w AS (
    PARTITION BY station_code
    ORDER BY observed_at
    ROWS BETWEEN 7 PRECEDING AND CURRENT ROW
  )
);

CREATE OR REPLACE TABLE daily_concentrations AS
SELECT
  h.station_code,
  -- SEMADET stamps the hour that just ended. 00:00 is the last hour of the
  -- previous civil day, so the 2025 workbook runs from 1 January 01:00
  -- through 1 January 2026 00:00 and still contains 365 days.
  CAST(h.observed_at - INTERVAL 1 HOUR AS DATE) AS day,
  AVG(h.pm10_ugm3) AS pm10_mean,
  COUNT(h.pm10_ugm3) AS pm10_n,
  AVG(h.pm25_ugm3) AS pm25_mean,
  COUNT(h.pm25_ugm3) AS pm25_n,
  MAX(h.o3_ppm) AS o3_max,
  COUNT(h.o3_ppm) AS o3_n,
  MAX(h.no2_ppm) AS no2_max,
  COUNT(h.no2_ppm) AS no2_n,
  MAX(h.so2_ppm) AS so2_max,
  COUNT(h.so2_ppm) AS so2_n,
  MAX(c.co_8h) AS co_max_8h,
  COUNT(c.co_8h) AS co_windows,
  COUNT(*) AS hours_rows
FROM hourly AS h
LEFT JOIN co_windows AS c
  ON h.station_code = c.station_code
 AND h.observed_at = c.observed_at
GROUP BY 1, 2
ORDER BY 1, 2;
"""


@dataclass(frozen=True)
class DailyStation:
    station_code: str
    station_name: str
    municipalities: str
    day: date
    pm10_mean: float | None
    pm10_n: int
    pm10_rounded: float | None
    pm10_band: str | None
    pm25_mean: float | None
    pm25_n: int
    pm25_rounded: float | None
    pm25_band: str | None
    o3_max: float | None
    o3_n: int
    o3_rounded: float | None
    o3_band: str | None
    no2_max: float | None
    no2_n: int
    no2_rounded: float | None
    no2_band: str | None
    so2_max: float | None
    so2_n: int
    so2_rounded: float | None
    so2_band: str | None
    co_max_8h: float | None
    co_windows: int
    co_rounded: float | None
    co_band: str | None
    band: str | None
    band_rank: int | None
    dominant_pollutant: str | None


def open_warehouse(hourly_csv: Path, database: Path) -> duckdb.DuckDBPyConnection:
    database.parent.mkdir(parents=True, exist_ok=True)
    if database.exists():
        database.unlink()
    connection = duckdb.connect(str(database))
    # DuckDB executes one statement per call.
    stripped = CONCENTRATION_SQL.strip()
    first, rest = stripped.split(";", 1)
    connection.execute(first + ";", [str(hourly_csv)])
    for statement in rest.split(";"):
        if statement.strip():
            connection.execute(statement)
    return connection


def build_daily_stations(
    connection: duckdb.DuckDBPyConnection,
    stations: dict[str, Station],
) -> list[DailyStation]:
    rows = connection.execute(
        """
        SELECT
          station_code, day,
          pm10_mean, pm10_n, pm25_mean, pm25_n,
          o3_max, o3_n, no2_max, no2_n, so2_max, so2_n,
          co_max_8h, co_windows
        FROM daily_concentrations
        ORDER BY station_code, day
        """
    ).fetchall()
    built: list[DailyStation] = []
    for row in rows:
        (
            code,
            day,
            pm10_mean,
            pm10_n,
            pm25_mean,
            pm25_n,
            o3_max,
            o3_n,
            no2_max,
            no2_n,
            so2_max,
            so2_n,
            co_max_8h,
            co_windows,
        ) = row
        observed_day = day if isinstance(day, date) else datetime.fromisoformat(str(day)).date()
        pm10_rounded, pm10_band = band_for(pm10_mean, "pm10", complete=pm10_n >= MIN_VALID_HOURS)
        pm25_rounded, pm25_band = band_for(pm25_mean, "pm25", complete=pm25_n >= MIN_VALID_HOURS)
        o3_rounded, o3_band = band_for(o3_max, "o3", complete=o3_n >= MIN_VALID_HOURS)
        no2_rounded, no2_band = band_for(no2_max, "no2", complete=no2_n >= MIN_VALID_HOURS)
        so2_rounded, so2_band = band_for(so2_max, "so2", complete=so2_n >= MIN_VALID_HOURS)
        co_rounded, co_band = band_for(co_max_8h, "co", complete=co_max_8h is not None)
        band, pollutant, rank = worst_band(
            {
                "pm10": pm10_band,
                "pm25": pm25_band,
                "o3": o3_band,
                "no2": no2_band,
                "so2": so2_band,
                "co": co_band,
            }
        )
        catalog = stations.get(code)
        built.append(
            DailyStation(
                station_code=code,
                station_name=display_name(stations, code),
                municipalities=catalog.municipalities if catalog else "",
                day=observed_day,
                pm10_mean=pm10_mean,
                pm10_n=int(pm10_n),
                pm10_rounded=pm10_rounded,
                pm10_band=pm10_band,
                pm25_mean=pm25_mean,
                pm25_n=int(pm25_n),
                pm25_rounded=pm25_rounded,
                pm25_band=pm25_band,
                o3_max=o3_max,
                o3_n=int(o3_n),
                o3_rounded=o3_rounded,
                o3_band=o3_band,
                no2_max=no2_max,
                no2_n=int(no2_n),
                no2_rounded=no2_rounded,
                no2_band=no2_band,
                so2_max=so2_max,
                so2_n=int(so2_n),
                so2_rounded=so2_rounded,
                so2_band=so2_band,
                co_max_8h=co_max_8h,
                co_windows=int(co_windows),
                co_rounded=co_rounded,
                co_band=co_band,
                band=band,
                band_rank=rank,
                dominant_pollutant=pollutant,
            )
        )
    return built


def write_daily_csv(rows: list[DailyStation], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "station_code",
        "station_name",
        "municipalities",
        "day",
        "pm10_mean_ugm3",
        "pm10_n",
        "pm10_rounded",
        "pm10_band",
        "pm25_mean_ugm3",
        "pm25_n",
        "pm25_rounded",
        "pm25_band",
        "o3_max_ppm",
        "o3_n",
        "o3_rounded_ppm",
        "o3_band",
        "no2_max_ppm",
        "no2_n",
        "no2_rounded_ppm",
        "no2_band",
        "so2_max_ppm",
        "so2_n",
        "so2_rounded_ppm",
        "so2_band",
        "co_max_8h_ppm",
        "co_windows",
        "co_rounded_ppm",
        "co_band",
        "band",
        "band_rank",
        "dominant_pollutant",
    ]
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "station_code": row.station_code,
                    "station_name": row.station_name,
                    "municipalities": row.municipalities,
                    "day": row.day.isoformat(),
                    "pm10_mean_ugm3": _fmt(row.pm10_mean, 4),
                    "pm10_n": row.pm10_n,
                    "pm10_rounded": _fmt(row.pm10_rounded, 0),
                    "pm10_band": row.pm10_band or "",
                    "pm25_mean_ugm3": _fmt(row.pm25_mean, 4),
                    "pm25_n": row.pm25_n,
                    "pm25_rounded": _fmt(row.pm25_rounded, 0),
                    "pm25_band": row.pm25_band or "",
                    "o3_max_ppm": _fmt(row.o3_max, 4),
                    "o3_n": row.o3_n,
                    "o3_rounded_ppm": _fmt(row.o3_rounded, 3),
                    "o3_band": row.o3_band or "",
                    "no2_max_ppm": _fmt(row.no2_max, 4),
                    "no2_n": row.no2_n,
                    "no2_rounded_ppm": _fmt(row.no2_rounded, 3),
                    "no2_band": row.no2_band or "",
                    "so2_max_ppm": _fmt(row.so2_max, 4),
                    "so2_n": row.so2_n,
                    "so2_rounded_ppm": _fmt(row.so2_rounded, 3),
                    "so2_band": row.so2_band or "",
                    "co_max_8h_ppm": _fmt(row.co_max_8h, 4),
                    "co_windows": row.co_windows,
                    "co_rounded_ppm": _fmt(row.co_rounded, 2),
                    "co_band": row.co_band or "",
                    "band": row.band or "",
                    "band_rank": "" if row.band_rank is None else row.band_rank,
                    "dominant_pollutant": row.dominant_pollutant or "",
                }
            )


def _fmt(value: float | None, digits: int) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"
