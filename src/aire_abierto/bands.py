"""Daily bands from NOM-172-SEMARNAT-2023 (DOF, 25 January 2024), tables 4–9.

Particles use the column that took effect in January 2026. Gases use the
single hourly (or 8-hour, for CO) columns in those tables.

The tables write "Buena" as a strict less-than and the next band as
"greater than" that same cut, so the exact cut is unnamed. After the
rounding the norm asks for, this project assigns that exact cut to the
worse of the two neighboring bands. Upper ends written as "a X" are
inclusive: 0.090 ppm of ozone stays Aceptable; the next ppm step is Mala.

This is a daily summary for the public. It is not the official hourly
Índice AIRE y SALUD. Particles are classified from the 24-hour mean (the
exposure the norm says the health risk refers to). The official hourly
index instead uses a 12-hour weighted average as an intraday warning, and
this project does not reproduce that weighted average.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

BANDS: tuple[str, ...] = (
    "buena",
    "aceptable",
    "mala",
    "muy_mala",
    "extremadamente_mala",
)

# Inclusive story after the exact-cut rule described above:
# value < edge[0] -> buena
# edge[0] <= value <= edge[1] -> aceptable
# edge[1] < value <= edge[2] -> mala
# edge[2] < value <= edge[3] -> muy_mala
# value > edge[3] -> extremadamente_mala
EDGES: dict[str, tuple[float, float, float, float]] = {
    "pm10": (45, 50, 132, 213),
    "pm25": (15, 25, 79, 130),
    "o3": (0.058, 0.090, 0.135, 0.175),
    "no2": (0.053, 0.106, 0.160, 0.213),
    "so2": (0.035, 0.075, 0.185, 0.304),
    "co": (5.00, 9.00, 12.00, 16.00),
}

DECIMALS: dict[str, int] = {
    "pm10": 0,
    "pm25": 0,
    "o3": 3,
    "no2": 3,
    "so2": 3,
    "co": 2,
}

# When two pollutants land on the same band, name the one earlier in this
# list. PM2.5 is first because of its weight in the health evidence the
# norm itself cites.
TIE_BREAK: tuple[str, ...] = ("pm25", "pm10", "o3", "no2", "co", "so2")

MIN_VALID_HOURS = 18


def round_half_up(value: float, decimals: int) -> float:
    quant = Decimal("1").scaleb(-decimals)
    rounded = Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP)
    return float(rounded)


def classify(value: float, pollutant: str) -> str:
    first, acceptable, poor, very_poor = EDGES[pollutant]
    if value < first:
        return "buena"
    if value <= acceptable:
        return "aceptable"
    if value <= poor:
        return "mala"
    if value <= very_poor:
        return "muy_mala"
    return "extremadamente_mala"


def band_for(value: float | None, pollutant: str, *, complete: bool) -> tuple[float | None, str | None]:
    if value is None or not complete:
        return None, None
    rounded = round_half_up(value, DECIMALS[pollutant])
    return rounded, classify(rounded, pollutant)


def worst_band(bands: dict[str, str | None]) -> tuple[str | None, str | None, int | None]:
    chosen_band: str | None = None
    chosen_pollutant: str | None = None
    chosen_rank = -1
    for pollutant in TIE_BREAK:
        band = bands.get(pollutant)
        if band is None:
            continue
        rank = BANDS.index(band)
        if rank > chosen_rank:
            chosen_rank = rank
            chosen_band = band
            chosen_pollutant = pollutant
    if chosen_band is None:
        return None, None, None
    return chosen_band, chosen_pollutant, chosen_rank
