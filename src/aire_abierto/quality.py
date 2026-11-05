"""Freshness, null rates, duplicates, and a unit sanity check.

Warnings stay visible and do not fail the build. A historical annual
workbook is expected to be weeks or months behind today's date. Failures
are reserved for files that cannot be read as air-quality measurements:
no rows, duplicate station-hours, units that do not match the published
scale, or a live year file that does not cover that year.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

import duckdb

POLLUTANTS = ("o3", "no2", "so2", "co", "pm10", "pm25")


@dataclass
class Check:
    id: str
    status: str
    detail_es: str
    detail_en: str
    metrics: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status,
            "detail_es": self.detail_es,
            "detail_en": self.detail_en,
            "metrics": self.metrics,
        }


@dataclass
class QualityReport:
    as_of: date
    data_kind: str
    checks: list[Check]
    summary: dict

    @property
    def ok(self) -> bool:
        return all(check.status != "fail" for check in self.checks)

    def as_dict(self) -> dict:
        return {
            "as_of": self.as_of.isoformat(),
            "data_kind": self.data_kind,
            "ok": self.ok,
            "summary": self.summary,
            "checks": [check.as_dict() for check in self.checks],
        }


def assess(
    connection: duckdb.DuckDBPyConnection,
    *,
    as_of: date,
    data_kind: str,
    year: int | None,
) -> QualityReport:
    summary = _summary(connection)
    checks = [
        _check_rows(summary),
        _check_duplicates(summary),
        _check_units(summary),
        _check_nulls(summary),
        _check_gaps(summary),
        _check_freshness(summary, as_of=as_of, data_kind=data_kind, year=year),
    ]
    return QualityReport(as_of=as_of, data_kind=data_kind, checks=checks, summary=summary)


def _summary(connection: duckdb.DuckDBPyConnection) -> dict:
    row = connection.execute(
        """
        SELECT
          COUNT(*) AS n,
          COUNT(DISTINCT station_code) AS stations,
          MIN(observed_at) AS min_ts,
          MAX(observed_at) AS max_ts,
          COUNT(DISTINCT CAST(observed_at AS DATE)) AS days,
          MEDIAN(o3_ppm) AS o3_median,
          MEDIAN(pm25_ugm3) AS pm25_median,
          MEDIAN(pm10_ugm3) AS pm10_median,
          1 - COUNT(o3_ppm) * 1.0 / NULLIF(COUNT(*), 0) AS o3_null_rate,
          1 - COUNT(no2_ppm) * 1.0 / NULLIF(COUNT(*), 0) AS no2_null_rate,
          1 - COUNT(so2_ppm) * 1.0 / NULLIF(COUNT(*), 0) AS so2_null_rate,
          1 - COUNT(co_ppm) * 1.0 / NULLIF(COUNT(*), 0) AS co_null_rate,
          1 - COUNT(pm10_ugm3) * 1.0 / NULLIF(COUNT(*), 0) AS pm10_null_rate,
          1 - COUNT(pm25_ugm3) * 1.0 / NULLIF(COUNT(*), 0) AS pm25_null_rate,
          COUNT(o3_flag) * 1.0 / NULLIF(COUNT(*), 0) AS o3_flag_rate,
          COUNT(no2_flag) * 1.0 / NULLIF(COUNT(*), 0) AS no2_flag_rate,
          COUNT(so2_flag) * 1.0 / NULLIF(COUNT(*), 0) AS so2_flag_rate,
          COUNT(co_flag) * 1.0 / NULLIF(COUNT(*), 0) AS co_flag_rate,
          COUNT(pm10_flag) * 1.0 / NULLIF(COUNT(*), 0) AS pm10_flag_rate,
          COUNT(pm25_flag) * 1.0 / NULLIF(COUNT(*), 0) AS pm25_flag_rate
        FROM hourly
        """
    ).fetchone()
    assert row is not None
    keys = [
        "n",
        "stations",
        "min_ts",
        "max_ts",
        "days",
        "o3_median",
        "pm25_median",
        "pm10_median",
        "o3_null_rate",
        "no2_null_rate",
        "so2_null_rate",
        "co_null_rate",
        "pm10_null_rate",
        "pm25_null_rate",
        "o3_flag_rate",
        "no2_flag_rate",
        "so2_flag_rate",
        "co_flag_rate",
        "pm10_flag_rate",
        "pm25_flag_rate",
    ]
    summary = dict(zip(keys, row, strict=True))
    duplicate = connection.execute(
        """
        SELECT COALESCE(SUM(extra), 0)
        FROM (
          SELECT COUNT(*) - 1 AS extra
          FROM hourly
          GROUP BY station_code, observed_at
          HAVING COUNT(*) > 1
        )
        """
    ).fetchone()
    summary["duplicate_keys"] = int(duplicate[0] if duplicate else 0)
    gaps = connection.execute(
        """
        WITH ordered AS (
          SELECT date_diff(
            'hour',
            lag(observed_at) OVER (PARTITION BY station_code ORDER BY observed_at),
            observed_at
          ) AS gap_hours
          FROM hourly
        )
        SELECT
          COUNT(*) FILTER (WHERE gap_hours IS NOT NULL) AS pairs,
          COUNT(*) FILTER (WHERE gap_hours IS NOT NULL AND gap_hours <> 1) AS bad_gaps
        FROM ordered
        """
    ).fetchone()
    summary["hour_pairs"] = int(gaps[0] if gaps else 0)
    summary["bad_hour_gaps"] = int(gaps[1] if gaps else 0)
    summary["min_ts"] = _iso(summary["min_ts"])
    summary["max_ts"] = _iso(summary["max_ts"])
    for key, value in list(summary.items()):
        if isinstance(value, float):
            summary[key] = round(value, 6)
    return summary


def _check_rows(summary: dict) -> Check:
    count = int(summary["n"])
    if count == 0:
        return Check(
            "row_count",
            "fail",
            "El archivo no tiene horas de medición.",
            "The file has no measurement hours.",
            {"rows": 0},
        )
    return Check(
        "row_count",
        "pass",
        f"{count} horas en {summary['stations']} estaciones.",
        f"{count} hours across {summary['stations']} stations.",
        {"rows": count, "stations": int(summary["stations"])},
    )


def _check_duplicates(summary: dict) -> Check:
    duplicates = int(summary["duplicate_keys"])
    if duplicates:
        return Check(
            "duplicate_keys",
            "fail",
            f"Hay {duplicates} horas repetidas para la misma estación.",
            f"{duplicates} repeated station-hours.",
            {"duplicate_keys": duplicates},
        )
    return Check(
        "duplicate_keys",
        "pass",
        "Cada estación tiene una sola fila por hora.",
        "Each station has one row per hour.",
        {"duplicate_keys": 0},
    )


def _check_units(summary: dict) -> Check:
    ozone = summary["o3_median"]
    pm25 = summary["pm25_median"]
    problems: list[str] = []
    if ozone is not None and (ozone > 1 or ozone < 0):
        problems.append("ozone")
    if pm25 is not None and pm25 > 1500:
        problems.append("pm25")
    if problems:
        return Check(
            "unit_sanity",
            "fail",
            "La mediana no cabe en las unidades publicadas (gases en ppm, partículas en µg/m³). "
            "Este proyecto no convierte la escala por su cuenta.",
            "The median does not fit the published units (gases in ppm, particles in µg/m³). "
            "This project does not convert the scale on its own.",
            {"problems": problems, "o3_median": ozone, "pm25_median": pm25},
        )
    return Check(
        "unit_sanity",
        "pass",
        "Las medianas caben en ppm para el ozono y en µg/m³ para PM2.5.",
        "The medians fit ppm for ozone and µg/m³ for PM2.5.",
        {"o3_median": ozone, "pm25_median": pm25, "pm10_median": summary["pm10_median"]},
    )


def _check_nulls(summary: dict) -> Check:
    rates = {name: summary[f"{name}_null_rate"] for name in POLLUTANTS}
    flags = {name: summary[f"{name}_flag_rate"] for name in POLLUTANTS}
    both_core_missing = (rates["o3"] or 0) > 0.95 and (rates["pm25"] or 0) > 0.95
    if both_core_missing:
        return Check(
            "null_rates",
            "fail",
            "Ozono y PM2.5 están vacíos en más del 95% de las horas. El archivo no alcanza para una lectura.",
            "Ozone and PM2.5 are empty in more than 95% of hours. The file cannot support a reading.",
            {"null_rates": rates, "flag_rates": flags},
        )
    high = [name for name, rate in rates.items() if rate is not None and rate > 0.5]
    if high:
        listed = ", ".join(high)
        return Check(
            "null_rates",
            "warn",
            f"Más de la mitad de las horas no tienen número válido en: {listed}. "
            "Esas horas suelen traer una bandera de SEMADET (ND, IO u otra) y no se inventan.",
            f"More than half of hours have no valid number for: {listed}. "
            "Those hours usually carry a SEMADET flag (ND, IO, or another) and are not filled in.",
            {"null_rates": rates, "flag_rates": flags},
        )
    return Check(
        "null_rates",
        "pass",
        "Ningún contaminante del índice supera 50% de horas sin número válido.",
        "No index pollutant is missing a valid number in more than half of hours.",
        {"null_rates": rates, "flag_rates": flags},
    )


def _check_gaps(summary: dict) -> Check:
    pairs = int(summary["hour_pairs"])
    bad = int(summary["bad_hour_gaps"])
    share = (bad / pairs) if pairs else 0
    metrics = {"hour_pairs": pairs, "bad_hour_gaps": bad, "bad_share": round(share, 6)}
    if pairs and share > 0.05:
        return Check(
            "hourly_continuity",
            "warn",
            "Más del 5% de los saltos entre horas seguidas de una estación no son de una hora. "
            "El promedio móvil de 8 horas del CO puede quedar incompleto.",
            "More than 5% of successive hours at a station are not one hour apart. "
            "The 8-hour CO average may be incomplete.",
            metrics,
        )
    return Check(
        "hourly_continuity",
        "pass",
        "Las horas de cada estación avanzan de una en una.",
        "Hours at each station step forward one at a time.",
        metrics,
    )


def _check_freshness(summary: dict, *, as_of: date, data_kind: str, year: int | None) -> Check:
    max_ts = summary["max_ts"]
    if not max_ts:
        return Check(
            "freshness",
            "fail",
            "No hay fecha máxima. No se puede hablar de frescura.",
            "There is no maximum timestamp, so freshness cannot be judged.",
            {},
        )
    max_dt = datetime.fromisoformat(max_ts)
    max_day = max_dt.date()
    # 00:00 is the closing hour of the previous civil day.
    civil_day = (max_dt - timedelta(hours=1)).date()
    age = (as_of - civil_day).days
    metrics = {
        "max_date": civil_day.isoformat(),
        "max_timestamp": max_ts,
        "min_date": summary["min_ts"],
        "age_days": age,
        "distinct_days": int(summary["days"]),
    }
    if data_kind == "synthetic":
        return Check(
            "freshness",
            "pass",
            "Los datos son inventados. La frescura no aplica.",
            "The rows are invented. Freshness does not apply.",
            metrics,
        )
    if data_kind == "official_workbook" and year is not None:
        min_day = datetime.fromisoformat(summary["min_ts"]).date() if summary["min_ts"] else max_day
        # The closing hour of 31 December is stamped 1 January 00:00 of the next year.
        covers_year = (
            min_day.year == year
            and max_day <= date(year + 1, 1, 1)
            and int(summary["days"]) >= 300
        )
        if not covers_year:
            return Check(
                "freshness",
                "fail",
                f"El archivo de {year} no cubre ese año "
                f"(de {min_day.isoformat()} a {max_day.isoformat()}, {summary['days']} fechas).",
                f"The {year} file does not cover that year "
                f"(from {min_day.isoformat()} to {max_day.isoformat()}, {summary['days']} dates).",
                metrics,
            )
    if age > 45:
        return Check(
            "freshness",
            "warn",
            f"El día civil más reciente es el {civil_day.isoformat()} ({age} días antes del {as_of.isoformat()}). "
            "El archivo anual de SEMADET es histórico. No sirve para decidir si hoy se puede correr al aire libre. "
            "Para el aire de hoy hay que abrir el reporte horario oficial.",
            f"The newest civil day is {civil_day.isoformat()} ({age} days before {as_of.isoformat()}). "
            "SEMADET's annual file is historical. It cannot say whether it is fine to exercise outside today. "
            "For today's air, open the official hourly report.",
            metrics,
        )
    return Check(
        "freshness",
        "pass",
        f"La hora más reciente es del {max_day.isoformat()} ({age} días).",
        f"The newest hour is {max_day.isoformat()} ({age} days).",
        metrics,
    )


def _iso(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(microsecond=0).isoformat()
    return str(value)
