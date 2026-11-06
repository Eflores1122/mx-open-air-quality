"""Coverage, freshness, and range checks for the livability mart."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


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

    @property
    def ok(self) -> bool:
        return all(check.status != "fail" for check in self.checks)

    def as_dict(self) -> dict:
        return {
            "as_of": self.as_of.isoformat(),
            "data_kind": self.data_kind,
            "ok": self.ok,
            "checks": [check.as_dict() for check in self.checks],
        }


def assess(rows: list[dict[str, object]], *, as_of: date, data_kind: str, warnings: list[str]) -> QualityReport:
    checks = [
        _rows(rows),
        _duplicates(rows),
        _ranges(rows),
        _coverage(rows, data_kind=data_kind),
        _freshness(rows, as_of=as_of, data_kind=data_kind),
        _warnings(warnings),
    ]
    return QualityReport(as_of=as_of, data_kind=data_kind, checks=checks)


def _rows(rows: list[dict[str, object]]) -> Check:
    if not rows:
        return Check("row_count", "fail", "El mart no tiene lugares.", "The mart has no places.", {"rows": 0})
    kinds = sorted({str(row["place_type"]) for row in rows})
    return Check(
        "row_count",
        "pass",
        f"{len(rows)} lugares ({', '.join(kinds)}).",
        f"{len(rows)} places ({', '.join(kinds)}).",
        {"rows": len(rows), "place_types": kinds},
    )


def _duplicates(rows: list[dict[str, object]]) -> Check:
    seen: set[str] = set()
    duplicates = 0
    for row in rows:
        key = str(row["place_id"])
        if key in seen:
            duplicates += 1
        seen.add(key)
    if duplicates:
        return Check(
            "duplicate_places",
            "fail",
            f"{duplicates} identificadores de lugar repetidos.",
            f"{duplicates} repeated place identifiers.",
            {"duplicates": duplicates},
        )
    return Check(
        "duplicate_places",
        "pass",
        "Cada lugar tiene un identificador.",
        "Each place has one identifier.",
        {"duplicates": 0},
    )


def _ranges(rows: list[dict[str, object]]) -> Check:
    problems: list[str] = []
    for row in rows:
        pm25 = _optional_float(row.get("air_pm25_median_ugm3"))
        if pm25 is not None and (pm25 < 0 or pm25 > 150):
            problems.append(f"pm25:{row['place_id']}")
        rate = _optional_float(row.get("lethal_per_100k"))
        if rate is not None and rate < 0:
            problems.append(f"rate:{row['place_id']}")
        perception = _optional_float(row.get("perception_insecurity_pct"))
        if perception is not None and (perception < 0 or perception > 100):
            problems.append(f"perception:{row['place_id']}")
        rent = _optional_float(row.get("enigh_imputed_rent_quarterly_mxn"))
        if rent is not None and rent <= 0:
            problems.append(f"rent:{row['place_id']}")
    if problems:
        return Check(
            "ranges",
            "fail",
            "Hay cifras fuera de un rango posible para estos indicadores.",
            "Some figures are outside a possible range for these indicators.",
            {"problems": problems[:20], "n": len(problems)},
        )
    return Check(
        "ranges",
        "pass",
        "PM2.5, tasas, percepción y renta caen en rangos posibles.",
        "PM2.5, rates, perception, and rent fall in possible ranges.",
        {"problems": 0},
    )


def _coverage(rows: list[dict[str, object]], *, data_kind: str) -> Check:
    def filled(column: str) -> int:
        return sum(1 for row in rows if str(row.get(column, "")).strip() != "")

    cities = [row for row in rows if row["place_type"] == "city"]
    metrics = {
        "places": len(rows),
        "cities": len(cities),
        "states": sum(1 for row in rows if row["place_type"] == "state"),
        "networks": sum(1 for row in rows if row["place_type"] == "network"),
        "with_air": filled("air_pm25_median_ugm3"),
        "with_safety": filled("lethal_per_100k"),
        "with_perception": filled("perception_insecurity_pct"),
        "with_rent": filled("enigh_imputed_rent_monthly_approx_mxn"),
        "with_quality_score": filled("score_quality"),
        "cities_with_perception": sum(1 for row in cities if str(row.get("perception_insecurity_pct", "")).strip()),
    }
    status = "pass"
    detail_es = "Hay lugares con aire, seguridad, percepción y renta aproximada."
    detail_en = "Places have air, safety, perception, and approximate rent."
    minimum_places = 2 if data_kind == "synthetic" else 30
    if metrics["with_safety"] == 0 or metrics["with_rent"] == 0 or metrics["places"] < minimum_places:
        status = "fail"
        detail_es = "Falta cobertura mínima de lugares, seguridad o renta."
        detail_en = "Minimum coverage of places, safety, or rent is missing."
    elif metrics["with_air"] == 0 or metrics["with_perception"] == 0:
        status = "warn"
        detail_es = "No hay aire o no hay percepción en este corte. Las otras piezas siguen."
        detail_en = "Air or perception is absent in this cut. The other pieces remain."
    return Check("coverage", status, detail_es, detail_en, metrics)


def _freshness(rows: list[dict[str, object]], *, as_of: date, data_kind: str) -> Check:
    if data_kind == "synthetic":
        return Check(
            "freshness",
            "pass",
            "Los datos son inventados. La frescura no aplica.",
            "The rows are invented. Freshness does not apply.",
            {},
        )
    air_years = [_optional_int(row.get("air_year")) for row in rows]
    air_years = [year for year in air_years if year]
    safety_years = [_optional_int(row.get("safety_year")) for row in rows]
    safety_years = [year for year in safety_years if year]
    rent_years = [_optional_int(row.get("rent_year")) for row in rows]
    rent_years = [year for year in rent_years if year]
    perception_periods = sorted({str(row.get("perception_period")) for row in rows if row.get("perception_period")})
    metrics = {
        "air_year_min": min(air_years) if air_years else None,
        "air_year_max": max(air_years) if air_years else None,
        "safety_year": max(safety_years) if safety_years else None,
        "rent_year": max(rent_years) if rent_years else None,
        "perception_periods": perception_periods,
        "as_of": as_of.isoformat(),
    }
    stale = False
    if air_years and (as_of.year - max(air_years) > 4 or as_of.year - min(air_years) > 4):
        stale = True
    if safety_years and as_of.year - max(safety_years) > 2:
        stale = True
    if stale:
        return Check(
            "freshness",
            "warn",
            "Alguna fuente tiene más de unos años. Sirve para comparar, no para decidir el mes que entra.",
            "At least one source is more than a couple of years old. It can compare places, not the coming month.",
            metrics,
        )
    return Check(
        "freshness",
        "pass",
        "Las vintages caben en la ventana usada para una comparación, no para un parte de hoy.",
        "The vintages fit the window used for a comparison, not for a bulletin about today.",
        metrics,
    )


def _warnings(warnings: list[str]) -> Check:
    if not warnings:
        return Check(
            "join_warnings",
            "pass",
            "Los cruces de nombres no dejaron huecos.",
            "The name joins left no gaps.",
            {"n": 0},
        )
    return Check(
        "join_warnings",
        "warn",
        f"{len(warnings)} cruces no encontraron municipio o ciudad. Esos pedazos no entran a la tasa.",
        f"{len(warnings)} joins missed a municipality or city. Those pieces are left out of the rate.",
        {"n": len(warnings), "sample": warnings[:25]},
    )


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return float(text)


def _optional_int(value: object) -> int | None:
    number = _optional_float(value)
    if number is None:
        return None
    return int(number)
