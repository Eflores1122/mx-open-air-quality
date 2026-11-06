"""Annual PM2.5 from an INECC SCICA hourly file.

SCICA publishes validated hourly concentrations for one monitoring
network and one year. Units in these PM2.5 files are micrograms per
cubic metre. This reader does not rescale them.

A station-day counts when at least 18 hours have a number. That is the
same hour rule this project already uses for particles, taken from the
daily reference in NOM-172-SEMARNAT-2023. A station-year counts when
valid days cover at least 75% of the days in that year. The network
figure is the median of those station-year means. The worst station is
kept beside it so a single hot monitor is not hidden.
"""

from __future__ import annotations

import csv
import math
import statistics
from datetime import date
from pathlib import Path

MIN_DAILY_HOURS = 18


def min_valid_days(year: int) -> int:
    days = 366 if _is_leap(year) else 365
    return math.ceil(0.75 * days)


def _is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def annual_pm25_from_hourly(path: Path, *, network_code: str, year: int) -> dict[str, object]:
    header, rows = _read_hourly(path)
    stations = [name for name in header if name not in {"Fecha", "Hora"}]
    # date -> station -> list of hourly numbers
    bucket: dict[str, dict[str, list[float]]] = {}
    for row in rows:
        day = (row.get("Fecha") or "").strip()
        if not day:
            continue
        by_station = bucket.setdefault(day, {name: [] for name in stations})
        for name in stations:
            number = _float_or_none(row.get(name))
            if number is None or number < 0:
                continue
            by_station[name].append(number)

    required_days = min_valid_days(year)
    station_means: list[tuple[str, float, int]] = []
    reporting = 0
    for name in stations:
        daily: list[float] = []
        saw_hour = False
        for by_station in bucket.values():
            hours = by_station.get(name) or []
            if hours:
                saw_hour = True
            if len(hours) >= MIN_DAILY_HOURS:
                daily.append(statistics.fmean(hours))
        if saw_hour:
            reporting += 1
        if len(daily) >= required_days:
            station_means.append((name, statistics.fmean(daily), len(daily)))

    station_means.sort(key=lambda item: item[1])
    median = statistics.median(item[1] for item in station_means) if station_means else None
    worst = station_means[-1] if station_means else None
    return {
        "network_code": network_code,
        "year": year,
        "pm25_median_ugm3": None if median is None else round(float(median), 4),
        "pm25_mean_ugm3": None
        if not station_means
        else round(statistics.fmean(item[1] for item in station_means), 4),
        "pm25_worst_ugm3": None if worst is None else round(worst[1], 4),
        "worst_station": "" if worst is None else worst[0],
        "stations_valid": len(station_means),
        "stations_in_file": reporting,
        "min_daily_hours": MIN_DAILY_HOURS,
        "min_valid_days": required_days,
        "days_in_file": len(bucket),
        "valid": bool(station_means),
    }


def semadet_annual_pm25(daily_station_csv: Path) -> dict[str, object] | None:
    """Median of station-year means from the existing Guadalajara metrics.

    Uses days that already passed the 18-hour rule (``pm25_n``). A station
    needs 75% of the days in its year. This series is not mixed into the
    SINAICA score. It is the same public SEMADET file, read the way this
    repository already reads it.
    """
    if not daily_station_csv.is_file():
        return None
    by_station: dict[str, list[tuple[date, float]]] = {}
    with daily_station_csv.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            raw = (row.get("pm25_mean_ugm3") or "").strip()
            hours = (row.get("pm25_n") or "").strip()
            if not raw or not hours:
                continue
            if int(float(hours)) < MIN_DAILY_HOURS:
                continue
            day = date.fromisoformat(row["day"])
            by_station.setdefault(row["station_code"], []).append((day, float(raw)))
    if not by_station:
        return None
    years = {day.year for pairs in by_station.values() for day, _ in pairs}
    year = max(years)
    required = min_valid_days(year)
    means: list[float] = []
    for pairs in by_station.values():
        in_year = [value for day, value in pairs if day.year == year]
        if len(in_year) >= required:
            means.append(statistics.fmean(in_year))
    if not means:
        return None
    return {
        "year": year,
        "pm25_median_ugm3": round(statistics.median(means), 4),
        "stations_valid": len(means),
        "min_valid_days": required,
        "source": "semadet_simaj",
    }


def _read_hourly(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        lines = handle.read().splitlines()
    start = 0
    for index, line in enumerate(lines):
        if line.startswith("Fecha,"):
            start = index
            break
    else:
        raise ValueError(f"No hourly header in {path}")
    reader = csv.DictReader(lines[start:])
    if not reader.fieldnames:
        raise ValueError(f"Empty hourly table in {path}")
    return list(reader.fieldnames), list(reader)


def _float_or_none(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None
