"""Daily metropolitan series and the station ranking."""

from __future__ import annotations

import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from aire_abierto.bands import BANDS
from aire_abierto.transform import DailyStation


def metro_rows(stations: list[DailyStation]) -> list[dict[str, object]]:
    by_day: dict = defaultdict(list)
    for row in stations:
        by_day[row.day].append(row)
    published: list[dict[str, object]] = []
    for day in sorted(by_day):
        rows = by_day[day]
        ranked = [row for row in rows if row.band is not None and row.band_rank is not None]
        ranked.sort(
            key=lambda row: (
                -(row.band_rank or 0),
                -(row.pm25_rounded or -1),
                row.station_code,
            )
        )
        worst = ranked[0] if ranked else None
        pm25_values = [
            row.pm25_mean for row in rows if row.pm25_mean is not None and row.pm25_n >= 18
        ]
        counts = Counter(row.band for row in ranked)
        published.append(
            {
                "day": day.isoformat(),
                "stations_with_index": len(ranked),
                "worst_band": worst.band if worst else "",
                "worst_band_rank": "" if worst is None or worst.band_rank is None else worst.band_rank,
                "worst_station_code": worst.station_code if worst else "",
                "worst_station_name": worst.station_name if worst else "",
                "dominant_pollutant": worst.dominant_pollutant if worst else "",
                "dominant_value": "" if worst is None else _dominant_value(worst),
                "median_pm25": "" if not pm25_values else f"{statistics.median(pm25_values):.4f}",
                "max_pm25": ""
                if not pm25_values
                else f"{max(pm25_values):.4f}",
                "stations_buena": counts.get("buena", 0),
                "stations_aceptable": counts.get("aceptable", 0),
                "stations_mala": counts.get("mala", 0),
                "stations_muy_mala": counts.get("muy_mala", 0),
                "stations_extremadamente_mala": counts.get("extremadamente_mala", 0),
            }
        )
    return published


def rank_rows(stations: list[DailyStation]) -> list[dict[str, object]]:
    grouped: dict[str, list[DailyStation]] = defaultdict(list)
    for row in stations:
        grouped[row.station_code].append(row)
    published: list[dict[str, object]] = []
    for code, rows in grouped.items():
        classified = [row for row in rows if row.band is not None]
        counts = Counter(row.band for row in classified)
        pm25_values = [
            row.pm25_mean for row in rows if row.pm25_mean is not None and row.pm25_n >= 18
        ]
        pm10_values = [
            row.pm10_mean for row in rows if row.pm10_mean is not None and row.pm10_n >= 18
        ]
        dominant = Counter(
            row.dominant_pollutant for row in classified if row.dominant_pollutant
        )
        days = len(classified)
        mala_or_worse = sum(counts.get(band, 0) for band in BANDS[2:])
        sample = rows[0]
        published.append(
            {
                "station_code": code,
                "station_name": sample.station_name,
                "municipalities": sample.municipalities,
                "days_with_index": days,
                "days_buena": counts.get("buena", 0),
                "days_aceptable": counts.get("aceptable", 0),
                "days_mala": counts.get("mala", 0),
                "days_muy_mala": counts.get("muy_mala", 0),
                "days_extremadamente_mala": counts.get("extremadamente_mala", 0),
                "days_mala_or_worse": mala_or_worse,
                "share_mala_or_worse": "" if not days else f"{mala_or_worse / days:.4f}",
                "mean_pm25": "" if not pm25_values else f"{statistics.fmean(pm25_values):.4f}",
                "max_pm25": "" if not pm25_values else f"{max(pm25_values):.4f}",
                "mean_pm10": "" if not pm10_values else f"{statistics.fmean(pm10_values):.4f}",
                "most_frequent_dominant": dominant.most_common(1)[0][0] if dominant else "",
            }
        )
    published.sort(
        key=lambda row: (
            -int(row["days_mala_or_worse"]),
            -float(row["mean_pm25"] or 0),
            str(row["station_code"]),
        )
    )
    return published


def write_dicts(rows: list[dict[str, object]], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else ["day"]
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _dominant_value(row: DailyStation) -> str:
    values = {
        "pm25": row.pm25_rounded,
        "pm10": row.pm10_rounded,
        "o3": row.o3_rounded,
        "no2": row.no2_rounded,
        "so2": row.so2_rounded,
        "co": row.co_rounded,
    }
    value = values.get(row.dominant_pollutant or "")
    if value is None:
        return ""
    digits = 0 if row.dominant_pollutant in {"pm10", "pm25"} else (2 if row.dominant_pollutant == "co" else 3)
    return f"{value:.{digits}f}"
