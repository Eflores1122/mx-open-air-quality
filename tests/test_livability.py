from datetime import date
from pathlib import Path

from aire_abierto.livability.air import annual_pm25_from_hourly, semadet_annual_pm25
from aire_abierto.livability.ensu import municipalities_from_catalog_rows, parse_perception_text
from aire_abierto.livability.pipeline import run_livability
from aire_abierto.livability.safety import aggregate_municipios
from aire_abierto.livability.scoring import combine, component_scores


def test_scores_use_fixed_ends_and_drop_missing_weights():
    components = component_scores(pm25_ugm3=5, high_harm_per_100k=0, insecurity_pct=0, rent_monthly_mxn=2_000)
    assert components == {"air": 100.0, "safety": 100.0, "perception": 100.0, "rent": 100.0}
    poor = component_scores(pm25_ugm3=35, high_harm_per_100k=80, insecurity_pct=100, rent_monthly_mxn=6_000)
    assert poor == {"air": 0.0, "safety": 0.0, "perception": 0.0, "rent": 0.0}
    mid = component_scores(pm25_ugm3=20, high_harm_per_100k=None, insecurity_pct=None, rent_monthly_mxn=None)
    score, used = combine(mid, {"air": 0.3, "safety": 0.3, "perception": 0.2, "rent": 0.2})
    assert used == {"air": 1.0}
    assert score == mid["air"]
    withheld, empty = combine(mid, {"air": 0.3, "safety": 0.3, "perception": 0.2, "rent": 0.2}, minimum=2)
    assert withheld is None
    assert empty == {}


def test_hourly_pm25_keeps_only_complete_stations(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("aire_abierto.livability.air.min_valid_days", lambda year: 2)
    lines = ["Concentraciones horarias para PM25 red SYN 2022", "Fecha,Hora,OK,SHORT"]
    for day, hours in (("2022-01-01", 18), ("2022-01-02", 18)):
        for hour in range(1, hours + 1):
            lines.append(f"{day},{hour},10,12")
    # A third day with too few hours must not create a valid day.
    lines.append("2022-01-03,1,10,12")
    path = tmp_path / "hourly.csv"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # The short station has only 1 hour on the extra day and 18 on the two full days,
    # so both stations are valid under the patched 2-day rule. Drop the short station's
    # second day to push it under the rule.
    text = path.read_text(encoding="utf-8").replace("2022-01-02,1,10,12", "2022-01-02,1,10,")
    path.write_text(text, encoding="utf-8")
    summary = annual_pm25_from_hourly(path, network_code="SYN", year=2022)
    assert summary["valid"] is True
    assert summary["stations_valid"] == 1
    assert summary["pm25_median_ugm3"] == 10.0
    assert summary["worst_station"] == "OK"


def test_semadet_summary_uses_the_existing_daily_file(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("aire_abierto.livability.air.min_valid_days", lambda year: 2)
    path = tmp_path / "daily_station.csv"
    rows = ["station_code,day,pm25_mean_ugm3,pm25_n"]
    for day in ("2025-01-01", "2025-01-02"):
        rows.append(f"CEN,{day},18,24")
        rows.append(f"MIR,{day},30,10")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    summary = semadet_annual_pm25(path)
    assert summary is not None
    assert summary["year"] == 2025
    assert summary["stations_valid"] == 1
    assert summary["pm25_median_ugm3"] == 18.0


def test_crime_basket_sums_modalities_and_skips_other_crimes():
    def row(subtype: str, kind: str, enero: int, year: int = 2025) -> dict:
        base = {month: 0 for month in (
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
        )}
        base.update(
            {
                "Ano": year,
                "Clave_Ent": "14",
                "Entidad": "Jalisco",
                "Cve. Municipio": 14039,
                "Municipio": "Guadalajara",
                "Tipo de delito": kind,
                "Subtipo de delito": subtype,
                "Enero": enero,
            }
        )
        return base

    aggregated = aggregate_municipios(
        [
            row("Homicidio doloso", "Homicidio", 2),
            row("Homicidio doloso", "Homicidio", 3),
            row("Homicidio culposo", "Homicidio", 9),
            row("Feminicidio", "Feminicidio", 1),
            row("Secuestro", "Secuestro", 4),
            row("Extorsión", "Extorsión", 5),
            row("Homicidio doloso", "Homicidio", 7, year=2024),
        ],
        year=2025,
    )
    assert len(aggregated) == 1
    assert aggregated[0]["homicidio_doloso"] == 5
    assert aggregated[0]["feminicidio"] == 1
    assert aggregated[0]["secuestro"] == 4
    assert aggregated[0]["extorsion"] == 5
    assert aggregated[0]["state_code"] == "14"


def test_perception_parser_reads_december_from_a_two_city_line():
    text = """
Septiembre Diciembre
Zapopan 50.2 53.1  5.8 Heroica Puebla de Zaragoza 76.2 75.5  -0.9
Cambio porcentual de otra sección que no debe entrar 10.0 11.0  1.0
"""
    rows = parse_perception_text(text, minimum_rows=1)
    by_name = {row["ensu_city"]: row for row in rows}
    assert by_name["Zapopan"]["december_pct"] == 53.1
    assert by_name["Heroica Puebla de Zaragoza"]["september_pct"] == 76.2
    assert "Cambio porcentual de otra sección que no debe entrar" not in by_name


def test_catalog_pads_a_dropped_zero_and_does_not_carry_the_previous_state():
    table = [
        ["Clave", "Nombre", "Clave", "Nombre", "Clave", "Nombre", "Clave", "Nombre", "CVEGEO"],
        ["52", "Mérida", "31", "Yucatán", "050", "Mérida", "0001", "Mérida", "310500001"],
        ["53", "Zacatecas", None, None, "017", "Guadalupe", "0001", "Guadalupe", "320170001"],
        [None, None, None, None, None, None, "0042", "La Zacatecana", None],
        ["06", "Saltillo", None, None, "027", "Ramos Arizpe", "0001", "Ramos Arizpe", "50270001"],
    ]
    rows = municipalities_from_catalog_rows(table)
    by_city = {}
    for row in rows:
        by_city.setdefault(row["ensu_city"], []).append(row["mun_code"])
    assert by_city["Zacatecas"] == [32017]
    assert 31017 not in by_city["Zacatecas"]
    assert by_city["Saltillo"] == [5027]
    saltillo = next(row for row in rows if row["ensu_city"] == "Saltillo")
    assert saltillo["state_code"] == "05"
    assert saltillo["cvegeo_example"] == "050270001"


def test_catalog_rows_forward_fill_the_city_and_rebuild_a_missing_cvegeo():
    table = [
        ["Clave", "Nombre", "Clave", "Nombre", "Clave", "Nombre", "Clave", "Nombre", "CVEGEO"],
        [
            "01",
            "Aguascalientes",
            "01",
            "Aguascalientes",
            "001",
            "Aguascalientes",
            "0001",
            "Aguascalientes",
            "010010001",
        ],
        [None, None, None, None, None, None, "1025", "Pocitos", None],
        ["03", "Tijuana", "02", "Baja California", "004", "Tijuana", "0001", "Tijuana", None],
    ]
    rows = municipalities_from_catalog_rows(table)
    codes = {(row["ensu_city"], row["mun_code"]) for row in rows}
    assert ("Aguascalientes", 1001) in codes
    assert ("Tijuana", 2004) in codes


def test_synthetic_mart_is_labeled_and_scores_the_example_city(tmp_path: Path):
    result = run_livability(source="synthetic", out_dir=tmp_path, as_of=date(2026, 11, 5))
    assert result["ok"] is True
    assert result["manifest"]["data_kind"] == "synthetic"
    assert result["manifest"]["not_official_advice"] is True
    city = next(row for row in result["mart"] if row["place_id"] == "city:ciudad-ejemplo")
    assert "invent" in city["note_es"].lower() or "inventado" in city["note_es"].lower()
    # 12 lethal deaths / 100,000 people = 12 per 100k.
    assert city["lethal_per_100k"] == 12.0
    assert city["perception_insecurity_pct"] == 50.0
    assert city["enigh_imputed_rent_monthly_approx_mxn"] == 3000.0
    assert city["score_quality"] != ""


def test_sample_excerpt_builds_a_national_mart(tmp_path: Path):
    result = run_livability(source="sample", out_dir=tmp_path, as_of=date(2026, 11, 5))
    assert result["ok"] is True
    assert result["manifest"]["data_kind"] == "official_excerpt"
    ids = [row["place_id"] for row in result["mart"]]
    assert len(ids) == len(set(ids))
    states = [row for row in result["mart"] if row["place_type"] == "state"]
    assert len(states) == 32
    cities = [row for row in result["mart"] if row["place_type"] == "city"]
    assert len(cities) >= 90
    zapopan = next(row for row in cities if row["place_name"] == "Zapopan")
    assert zapopan["perception_insecurity_pct"] == 53.1
    saltillo = next(row for row in cities if row["place_name"] == "Saltillo")
    assert saltillo["safety_coverage"] == 1.0
    assert saltillo["lethal_per_100k"] != ""
    zacatecas = next(row for row in cities if row["place_name"] == "Zacatecas")
    assert zacatecas["state_name"] == "Zacatecas"
    assert zacatecas["enigh_imputed_rent_quarterly_mxn"] == 5658.0
    jalisco = next(row for row in states if row["state_name"] == "Jalisco")
    assert jalisco["enigh_imputed_rent_quarterly_mxn"] == 9694
    assert jalisco["lethal_per_100k"] != ""
    assert (tmp_path / "place_mart.csv").is_file()
    assert (tmp_path / "place_municipalities.csv").is_file()
