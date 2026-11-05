"""Invented hourly file with the same columns as a SEMADET extract.

These numbers are not measurements. They exist so the pipeline, the tests,
and CI can run when the public workbook cannot be downloaded. Stations use
the SYN- prefix and the manifest says the file is synthetic.
"""

from __future__ import annotations

import csv
from datetime import datetime, timedelta
from pathlib import Path

from aire_abierto.stations import Station

_SOURCE_COLUMNS = (
    "STATION",
    "DATE",
    "HOUR",
    "O3",
    "NO2",
    "SO2",
    "CO",
    "PM10",
    "PM2.5",
)

SYNTHETIC_STATIONS = {
    "SYN-NORTE": Station(
        code="SYN-NORTE",
        name="Estación sintética norte",
        municipalities="ninguno; dato inventado",
        notes="No es una estación del SIMAJ.",
    ),
    "SYN-SUR": Station(
        code="SYN-SUR",
        name="Estación sintética sur",
        municipalities="ninguno; dato inventado",
        notes="No es una estación del SIMAJ.",
    ),
}

# Constant hours, chosen so the southern station falls in Mala on PM2.5
# and the northern station stays in Buena. Flags on SO2 show the null path.
_PROFILES = {
    "SYN-NORTE": {
        "o3": 0.030,
        "no2": 0.020,
        "so2": None,
        "co": 0.40,
        "pm10": 30,
        "pm25": 12,
    },
    "SYN-SUR": {
        "o3": 0.100,
        "no2": 0.040,
        "so2": 0.010,
        "co": 0.80,
        "pm10": 80,
        "pm25": 48,
    },
}


def write_synthetic_csv(destination: Path, *, days: int = 7, start: datetime | None = None) -> int:
    destination.parent.mkdir(parents=True, exist_ok=True)
    origin = start or datetime(2025, 5, 1, 0, 0, 0)
    count = 0
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(_SOURCE_COLUMNS))
        writer.writeheader()
        for station, profile in _PROFILES.items():
            for day_index in range(days):
                for hour in range(24):
                    observed = origin + timedelta(days=day_index, hours=hour)
                    writer.writerow(
                        {
                            "STATION": station,
                            "DATE": observed.strftime("%Y-%m-%d %H:%M:%S"),
                            "HOUR": hour,
                            "O3": profile["o3"],
                            "NO2": profile["no2"],
                            "SO2": "ND" if profile["so2"] is None else profile["so2"],
                            "CO": profile["co"],
                            "PM10": profile["pm10"],
                            "PM2.5": profile["pm25"],
                        }
                    )
                    count += 1
    return count
