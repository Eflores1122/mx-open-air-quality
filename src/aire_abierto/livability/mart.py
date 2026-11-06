"""City, network, and state mart. Rates are a DuckDB join.

The bridge table lists every municipality that belongs to a place.
DuckDB sums crime counts and CONAPO population on that bridge. A place
keeps a rate when at least 90% of its municipalities match both files.
The score then uses homicidio doloso plus feminicidio per 100,000.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

import duckdb

from aire_abierto.livability.scoring import COMBINED_WEIGHTS, QUALITY_WEIGHTS, combine, component_scores
from aire_abierto.livability.textutil import normalize_name

MATCH_FLOOR = 0.90


@dataclass
class Bundle:
    networks: list[dict[str, str]]
    air: list[dict[str, str]]
    crime: list[dict[str, str]]
    population: list[dict[str, str]]
    perception: list[dict[str, str]]
    catalog: list[dict[str, str]]
    rent: list[dict[str, str]]
    semadet: dict[str, object] | None = None
    data_kind: str = "official_excerpt"
    warnings: list[str] = field(default_factory=list)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def assemble_mart(bundle: Bundle) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    places, bridge, gaps = _places(bundle)
    rates = _rates(bridge, bundle.crime, bundle.population)
    rent_by_state = {
        normalize_name(row["state_name"]): row
        for row in bundle.rent
        if normalize_name(row["state_name"]) != "estados unidos mexicanos"
    }
    air_by_code = {row["network_code"]: row for row in bundle.air}
    attached: dict[str, dict[str, str]] = {}
    for network in bundle.networks:
        code = network["network_code"]
        air = air_by_code.get(code)
        target = (network.get("attach_ensu_city") or "").strip()
        if target and air and str(air.get("valid", "")).lower() in {"true", "1"}:
            key = normalize_name(target)
            current = attached.get(key)
            if current is None or int(float(air.get("stations_valid") or 0)) > int(
                float(current.get("stations_valid") or 0)
            ):
                attached[key] = {**air, "note_es": network.get("note_es", ""), "note_en": network.get("note_en", "")}
            else:
                bundle.warnings.append(f"air-not-attached:{code}")

    mart: list[dict[str, object]] = []
    for place in places:
        rate = rates.get(place["place_id"])
        if place.get("safety_same_as"):
            rate = rates.get(str(place["safety_same_as"]))
        row = _compose(place, rate, rent_by_state, attached, bundle)
        mart.append(row)
    mart.sort(key=lambda item: (str(item["place_type"]), str(item["place_name"])))
    for gap in gaps:
        bundle.warnings.append(gap)
    return mart, bridge


def _places(bundle: Bundle) -> tuple[list[dict[str, object]], list[dict[str, object]], list[str]]:
    catalog_by_city: dict[str, list[dict[str, str]]] = {}
    for row in bundle.catalog:
        catalog_by_city.setdefault(normalize_name(row["ensu_city"]), []).append(row)
    mun_by_state_name: dict[str, list[dict[str, str]]] = {}
    state_code_by_name: dict[str, str] = {}
    for row in bundle.population:
        mun_by_state_name.setdefault(normalize_name(row["state_name"]), []).append(row)
        state_code_by_name[normalize_name(row["state_name"])] = row["state_code"]

    places: list[dict[str, object]] = []
    bridge: list[dict[str, object]] = []
    gaps: list[str] = []
    city_ids: dict[str, str] = {}

    for row in bundle.perception:
        if normalize_name(row["ensu_city"]) == "nacional":
            continue
        key = normalize_name(row["ensu_city"])
        muns = catalog_by_city.get(key, [])
        if not muns:
            gaps.append(f"ensu-without-catalog:{row['ensu_city']}")
            state_name = ""
            state_code = ""
        else:
            state_names: list[str] = []
            for mun in muns:
                if mun["state_name"] not in state_names:
                    state_names.append(mun["state_name"])
            if len(state_names) > 1:
                state_name = " / ".join(state_names)
                state_code = ""
            else:
                state_name = state_names[0]
                state_code = muns[0]["state_code"]
        place_id = f"city:{_slug(row['ensu_city'])}"
        city_ids[key] = place_id
        places.append(
            {
                "place_id": place_id,
                "place_name": row["ensu_city"],
                "place_type": "city",
                "state_code": state_code,
                "state_name": state_name,
                "ensu_city": row["ensu_city"],
                "perception": row,
                "safety_geography": "ensu_municipalities" if muns else "none",
                "safety_same_as": "",
                "network_code": "",
                "crosswalk_note_es": "",
                "crosswalk_note_en": "",
            }
        )
        for mun in muns:
            bridge.append({"place_id": place_id, "mun_code": int(mun["mun_code"]), "mun_name": mun["mun_name"]})

    for state_name_key, muns in mun_by_state_name.items():
        state_code = muns[0]["state_code"]
        state_name = muns[0]["state_name"]
        place_id = f"state:{state_code}"
        places.append(
            {
                "place_id": place_id,
                "place_name": state_name,
                "place_type": "state",
                "state_code": state_code,
                "state_name": state_name,
                "ensu_city": "",
                "perception": None,
                "safety_geography": "state",
                "safety_same_as": "",
                "network_code": "",
                "crosswalk_note_es": "",
                "crosswalk_note_en": "",
            }
        )
        for mun in muns:
            bridge.append({"place_id": place_id, "mun_code": int(mun["mun_code"]), "mun_name": mun["mun_name"]})

    state_place = {row["state_code"]: f"state:{row['state_code']}" for row in places if row["place_type"] == "state"}
    for network in bundle.networks:
        if (network.get("attach_ensu_city") or "").strip():
            continue
        state_name = (network.get("state_name") or "").strip()
        state_code = state_code_by_name.get(normalize_name(state_name), "")
        place_id = f"network:{network['network_code']}"
        mode = (network.get("safety_mode") or "none").strip()
        safety_same_as = ""
        geography = "none"
        if mode == "state" and state_code:
            safety_same_as = state_place.get(state_code, "")
            geography = "state"
        elif mode == "ensu_cities":
            geography = "ensu_cities"
            for city in _pipes(network.get("safety_ensu_cities", "")):
                found = city_ids.get(normalize_name(city))
                if not found:
                    gaps.append(f"network-ensu-miss:{network['network_code']}:{city}")
                    continue
                for link in [item for item in bridge if item["place_id"] == found]:
                    bridge.append(
                        {"place_id": place_id, "mun_code": int(link["mun_code"]), "mun_name": link["mun_name"]}
                    )
        elif mode == "municipality":
            geography = "municipality"
            for name in _pipes(network.get("safety_mun_names", "")):
                code = _resolve_mun(name, state_name, bundle.population)
                if code is None:
                    gaps.append(f"mun-miss:{network['network_code']}:{name}")
                    continue
                bridge.append({"place_id": place_id, "mun_code": code, "mun_name": name})
        places.append(
            {
                "place_id": place_id,
                "place_name": network["place_name"],
                "place_type": "network",
                "state_code": state_code,
                "state_name": state_name,
                "ensu_city": "",
                "perception": None,
                "safety_geography": geography,
                "safety_same_as": safety_same_as,
                "network_code": network["network_code"],
                "crosswalk_note_es": network.get("note_es", ""),
                "crosswalk_note_en": network.get("note_en", ""),
            }
        )
    # Drop duplicate municipality links created when several ENSU cities share one.
    unique_bridge: dict[tuple[str, int], dict[str, object]] = {}
    for link in bridge:
        unique_bridge[(str(link["place_id"]), int(link["mun_code"]))] = link
    return places, list(unique_bridge.values()), gaps


def _rates(
    bridge: list[dict[str, object]],
    crime: list[dict[str, str]],
    population: list[dict[str, str]],
) -> dict[str, dict[str, object]]:
    connection = duckdb.connect()
    try:
        connection.execute(
            """
            CREATE TABLE bridge (place_id VARCHAR, mun_code INTEGER, mun_name VARCHAR);
            CREATE TABLE crime (
              mun_code INTEGER, homicidio_doloso INTEGER, feminicidio INTEGER,
              secuestro INTEGER, extorsion INTEGER
            );
            CREATE TABLE population (mun_code INTEGER, population BIGINT);
            """
        )
        connection.executemany(
            "INSERT INTO bridge VALUES (?, ?, ?)",
            [(row["place_id"], int(row["mun_code"]), row["mun_name"]) for row in bridge],
        )
        connection.executemany(
            "INSERT INTO crime VALUES (?, ?, ?, ?, ?)",
            [
                (
                    int(row["mun_code"]),
                    int(float(row["homicidio_doloso"])),
                    int(float(row["feminicidio"])),
                    int(float(row["secuestro"])),
                    int(float(row["extorsion"])),
                )
                for row in crime
            ],
        )
        connection.executemany(
            "INSERT INTO population VALUES (?, ?)",
            [(int(row["mun_code"]), int(float(row["population"]))) for row in population],
        )
        summed = connection.execute(
            """
            SELECT
              b.place_id,
              COUNT(*) AS muns_requested,
              COUNT(c.mun_code) AS muns_with_crime,
              COUNT(p.mun_code) AS muns_with_population,
              COUNT(*) FILTER (WHERE c.mun_code IS NOT NULL AND p.mun_code IS NOT NULL) AS muns_matched,
              COALESCE(SUM(c.homicidio_doloso) FILTER (WHERE p.mun_code IS NOT NULL), 0) AS homicidio_doloso,
              COALESCE(SUM(c.feminicidio) FILTER (WHERE p.mun_code IS NOT NULL), 0) AS feminicidio,
              COALESCE(SUM(c.secuestro) FILTER (WHERE p.mun_code IS NOT NULL), 0) AS secuestro,
              COALESCE(SUM(c.extorsion) FILTER (WHERE p.mun_code IS NOT NULL), 0) AS extorsion,
              COALESCE(SUM(p.population) FILTER (WHERE c.mun_code IS NOT NULL), 0) AS population
            FROM bridge b
            LEFT JOIN crime c ON b.mun_code = c.mun_code
            LEFT JOIN population p ON b.mun_code = p.mun_code
            GROUP BY b.place_id
            """
        ).fetchall()
    finally:
        connection.close()
    columns = (
        "place_id",
        "muns_requested",
        "muns_with_crime",
        "muns_with_population",
        "muns_matched",
        "homicidio_doloso",
        "feminicidio",
        "secuestro",
        "extorsion",
        "population",
    )
    published: dict[str, dict[str, object]] = {}
    for record in summed:
        item = dict(zip(columns, record, strict=True))
        requested = int(item["muns_requested"])
        matched = int(item["muns_matched"])
        population_used = int(item["population"])
        cover = (matched / requested) if requested else 0.0
        item["coverage"] = round(cover, 4)
        lethal = int(item["homicidio_doloso"]) + int(item["feminicidio"])
        item["lethal_count"] = lethal
        if requested and cover >= MATCH_FLOOR and population_used > 0:
            item["lethal_per_100k"] = round(lethal * 100_000 / population_used, 4)
            item["secuestro_per_100k"] = round(int(item["secuestro"]) * 100_000 / population_used, 4)
            item["extorsion_per_100k"] = round(int(item["extorsion"]) * 100_000 / population_used, 4)
        else:
            item["lethal_per_100k"] = None
            item["secuestro_per_100k"] = None
            item["extorsion_per_100k"] = None
        published[str(item["place_id"])] = item
    return published


def _compose(
    place: dict[str, object],
    rate: dict[str, object] | None,
    rent_by_state: dict[str, dict[str, str]],
    attached_air: dict[str, dict[str, str]],
    bundle: Bundle,
) -> dict[str, object]:
    air = None
    if place["place_type"] == "network" and place["network_code"]:
        found = next((row for row in bundle.air if row["network_code"] == place["network_code"]), None)
        if found and str(found.get("valid", "")).lower() in {"true", "1"}:
            air = found
    elif place["place_type"] == "city":
        air = attached_air.get(normalize_name(str(place["ensu_city"])))
    rent = rent_by_state.get(normalize_name(str(place["state_name"])))
    perception = place["perception"]
    pm25 = _num(air.get("pm25_median_ugm3")) if air else None
    insecurity = _num(perception.get("december_pct")) if isinstance(perception, dict) else None
    quarterly = _num(rent.get("imputed_rent_quarterly_mxn")) if rent else None
    monthly = None if quarterly is None else round(quarterly / 3.0, 2)
    lethal_rate = None if rate is None else rate.get("lethal_per_100k")
    lethal_rate_f = None if lethal_rate is None else float(lethal_rate)
    components = component_scores(
        pm25_ugm3=pm25,
        high_harm_per_100k=lethal_rate_f,
        insecurity_pct=insecurity,
        rent_monthly_mxn=monthly,
    )
    quality, quality_weights = combine(components, QUALITY_WEIGHTS, minimum=2)
    combined, combined_weights = combine(components, COMBINED_WEIGHTS, minimum=2)
    semadet = bundle.semadet if place["network_code"] == "GDL" else None
    note_es, note_en = _notes(place, air, rate, rent is not None, perception is not None, semadet)
    return {
        "place_id": place["place_id"],
        "place_name": place["place_name"],
        "place_type": place["place_type"],
        "state_code": place["state_code"],
        "state_name": place["state_name"],
        "data_kind": bundle.data_kind,
        "air_network_code": "" if air is None else air.get("network_code", ""),
        "air_year": "" if air is None else air.get("year", ""),
        "air_pm25_median_ugm3": "" if pm25 is None else round(pm25, 4),
        "air_pm25_worst_ugm3": "" if air is None else air.get("pm25_worst_ugm3", ""),
        "air_stations_valid": "" if air is None else air.get("stations_valid", ""),
        "air_stations_in_file": "" if air is None else air.get("stations_in_file", ""),
        "semadet_year": "" if not semadet else semadet.get("year", ""),
        "semadet_pm25_median_ugm3": "" if not semadet else semadet.get("pm25_median_ugm3", ""),
        "semadet_stations_valid": "" if not semadet else semadet.get("stations_valid", ""),
        "safety_year": "" if rate is None or lethal_rate is None else _crime_year(bundle),
        "safety_geography": place["safety_geography"],
        "safety_population": "" if rate is None or lethal_rate is None else rate.get("population", ""),
        "safety_coverage": "" if rate is None else rate.get("coverage", ""),
        "homicidio_doloso": "" if rate is None or lethal_rate is None else rate.get("homicidio_doloso", ""),
        "feminicidio": "" if rate is None or lethal_rate is None else rate.get("feminicidio", ""),
        "secuestro": "" if rate is None or lethal_rate is None else rate.get("secuestro", ""),
        "extorsion": "" if rate is None or lethal_rate is None else rate.get("extorsion", ""),
        "lethal_per_100k": "" if lethal_rate is None else lethal_rate,
        "secuestro_per_100k": _blank(rate, "secuestro_per_100k"),
        "extorsion_per_100k": _blank(rate, "extorsion_per_100k"),
        "perception_period": "" if not isinstance(perception, dict) else perception.get("period", ""),
        "perception_insecurity_pct": "" if insecurity is None else insecurity,
        "rent_year": "" if rent is None else rent.get("year", ""),
        "rent_geography": "" if rent is None else "state",
        "enigh_imputed_rent_quarterly_mxn": "" if quarterly is None else quarterly,
        "enigh_imputed_rent_monthly_approx_mxn": "" if monthly is None else monthly,
        "score_air": _round(components["air"]),
        "score_safety": _round(components["safety"]),
        "score_perception": _round(components["perception"]),
        "score_rent": _round(components["rent"]),
        "score_quality": _round(quality),
        "score_combined": _round(combined),
        "note_es": note_es,
        "note_en": note_en,
        "quality_weights": _weight_text(quality_weights),
        "combined_weights": _weight_text(combined_weights),
    }


def _notes(
    place: dict[str, object],
    air: dict[str, str] | None,
    rate: dict[str, object] | None,
    has_rent: bool,
    has_perception: bool,
    semadet: dict[str, object] | None,
) -> tuple[str, str]:
    es: list[str] = []
    en: list[str] = []
    if air:
        es.append(
            f"Aire: mediana anual de PM2.5 de la red {air.get('network_code')} en {air.get('year')} "
            f"({air.get('stations_valid')} estaciones con suficientes días). No es el aire de hoy."
        )
        en.append(
            f"Air: annual median PM2.5 from network {air.get('network_code')} in {air.get('year')} "
            f"({air.get('stations_valid')} stations with enough days). This is not today's air."
        )
        if air.get("note_es"):
            es.append(str(air["note_es"]))
            en.append(str(air.get("note_en") or ""))
    if place.get("crosswalk_note_es"):
        es.append(str(place["crosswalk_note_es"]))
        en.append(str(place["crosswalk_note_en"]))
    if rate is not None and rate.get("lethal_per_100k") is not None:
        es.append(
            "Seguridad: homicidios dolosos más feminicidios en 2025 por 100 mil habitantes "
            f"(geografía: {place['safety_geography']}). El secuestro y la extorsión se publican aparte "
            "y no entran al puntaje, porque el registro cambia mucho entre fiscalías."
        )
        en.append(
            "Safety: intentional homicides plus feminicides in 2025 per 100,000 people "
            f"(geography: {place['safety_geography']}). Kidnapping and extortion are published separately "
            "and stay out of the score, because recording practices differ across prosecutors."
        )
    if has_perception:
        es.append(
            "Percepción: ENSU, diciembre de 2024, porcentaje de personas de 18 años y más que considera "
            "inseguro vivir en su ciudad. El margen de error de una ciudad puede ser amplio."
        )
        en.append(
            "Perception: ENSU, December 2024, share of people 18 and older who say living in their city "
            "is unsafe. The margin of error for one city can be wide."
        )
    if has_rent:
        es.append(
            "Renta aproximada: ENIGH 2024, estimación del alquiler de la vivienda, promedio trimestral "
            "por hogar en el estado, dividido entre 3. Incluye a quien no paga renta. No es un anuncio "
            "ni la renta de esta ciudad, y no dice si el salario local alcanza."
        )
        en.append(
            "Approximate rent: ENIGH 2024 imputed housing rent, the state average per household for a "
            "quarter, divided by 3. It includes households that do not pay rent. It is not a listing "
            "and it is not this city's rent, and it does not say whether local earnings cover it."
        )
    if semadet:
        es.append(
            f"Guadalajara también tiene el archivo SEMADET de {semadet.get('year')}: mediana de PM2.5 "
            f"{semadet.get('pm25_median_ugm3')} µg/m³ en {semadet.get('stations_valid')} estaciones. "
            "Esa cifra no entra al puntaje nacional, que usa SINAICA para poder comparar redes."
        )
        en.append(
            f"Guadalajara also has the SEMADET file for {semadet.get('year')}: median PM2.5 "
            f"{semadet.get('pm25_median_ugm3')} µg/m³ across {semadet.get('stations_valid')} stations. "
            "That figure is not in the national score, which uses SINAICA so networks can be compared."
        )
    if not es:
        es.append("Este lugar no tiene métricas en los extractos.")
        en.append("This place has no metrics in the excerpts.")
    return " ".join(es), " ".join(en)


def _resolve_mun(name: str, state_name: str, population: list[dict[str, str]]) -> int | None:
    target = normalize_name(name)
    state_key = normalize_name(state_name)
    in_state = [row for row in population if normalize_name(row["state_name"]) == state_key]
    exact = [row for row in in_state if normalize_name(row["mun_name"]) == target]
    if len(exact) == 1:
        return int(exact[0]["mun_code"])
    starts = [row for row in in_state if normalize_name(row["mun_name"]).startswith(target)]
    if len(starts) == 1:
        return int(starts[0]["mun_code"])
    return None


def _crime_year(bundle: Bundle) -> str:
    if not bundle.crime:
        return ""
    return str(bundle.crime[0].get("year", ""))


def _pipes(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split("|") if part.strip()]


def _slug(value: str) -> str:
    text = normalize_name(value)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def _blank(rate: dict[str, object] | None, key: str) -> object:
    if rate is None or rate.get(key) is None:
        return ""
    return rate[key]


def _num(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.lower() == "none":
        return None
    return float(text)


def _round(value: float | None) -> str | float:
    if value is None:
        return ""
    return round(value, 2)


def _weight_text(weights: dict[str, float]) -> str:
    if not weights:
        return ""
    return ";".join(f"{key}:{weight:.3f}" for key, weight in weights.items())
