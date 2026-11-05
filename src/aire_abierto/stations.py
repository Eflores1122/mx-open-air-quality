"""SIMAJ station names published by SEMADET.

Codes AGU through VAL match the nomenclature in the SEMADET daily report
(aire.jalisco.gob.mx/info/numeraliaimeca.pdf) and the state's contingency
documents. The 2025 workbook uses SMT for the station the current public
station list calls Santa Margarita. Older SEMADET documents used SMA for
that same name. No other code in the 2025 file is left unmatched, so this
catalog maps SMT to Santa Margarita and says so in ``notes``.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from aire_abierto.paths import station_catalog


@dataclass(frozen=True)
class Station:
    code: str
    name: str
    municipalities: str
    notes: str = ""


def load_stations(path: Path | None = None) -> dict[str, Station]:
    catalog = path or station_catalog()
    stations: dict[str, Station] = {}
    with catalog.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            code = row["station_code"].strip().upper()
            stations[code] = Station(
                code=code,
                name=row["name"].strip(),
                municipalities=row["municipalities"].strip(),
                notes=(row.get("notes") or "").strip(),
            )
    return stations


def display_name(stations: dict[str, Station], code: str) -> str:
    found = stations.get(code.upper())
    return found.name if found else code
