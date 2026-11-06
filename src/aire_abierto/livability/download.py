"""Refresh the public excerpts. CI does not run this module.

Official hosts, in the order this file tries them:

- Air: INECC SCICA form at http://scica.inecc.gob.mx/exec/addl
  (validated hourly PM2.5, one network and one year at a time).
- Crime: datos.gob.mx datastore for the SESNSP municipal file
  (CC BY 4.0). The direct CSV on repodatos.atdt.gob.mx returned 403
  from the environment that built the committed excerpt.
- Population: CONAPO mid-year municipal projections on datos.gob.mx.
- ENSU perception: the December 2024 executive PDF, the edition whose
  city table is still text. The December 2025 chart did not keep city
  names in the text layer.
- ENSU municipalities: the 2025 city catalog PDF. Refreshing it needs
  the optional ``pdfplumber`` package.

ENIGH imputed rent is a small committed transcription of the published
state table. The interactive page needs a browser, so this module does
not re-download it. See ``data/livability/samples/PROVENANCE.md``.
"""

from __future__ import annotations

import csv
import json
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from aire_abierto.livability.air import annual_pm25_from_hourly
from aire_abierto.livability.ensu import municipalities_from_catalog_rows, parse_perception_text
from aire_abierto.livability.safety import EXTORSION, FEMINICIDIO, SECUESTRO, aggregate_municipios, month_total

USER_AGENT = "aire-abierto/0.2 (civic open-data; public INECC, SESNSP, CONAPO, INEGI)"
SCICA_NETWORKS = "http://scica.inecc.gob.mx/exec/jx_nwkbyct"
SCICA_YEARS = "http://scica.inecc.gob.mx/exec/jx_yrbynkct"
SCICA_HOURLY = "http://scica.inecc.gob.mx/exec/addl"
SESNSP_SEARCH = "https://www.datos.gob.mx/api/3/action/datastore_search"
SESNSP_RESOURCE = "57fbd692-3e5c-4b1b-8621-694cb3a33035"
SESNSP_DATASET = "https://www.datos.gob.mx/dataset/incidencia_delictiva"
CONAPO_POPULATION = (
    "https://www.datos.gob.mx/dataset/f2b9b220-3ef7-4e3a-bde6-87e1dac78c6a/resource/"
    "e9160552-769b-41ee-88d1-afc765552608/download/pobproy_inddemo.csv"
)
ENSU_PERCEPTION_PDF = (
    "https://www.inegi.org.mx/contenidos/programas/ensu/doc/ensu2024_diciembre_presentacion_ejecutiva.pdf"
)
ENSU_CATALOG_PDF = "https://www.inegi.org.mx/contenidos/programas/ensu/doc/ensu2025_catalogo_ciudades_interes.pdf"

CRIME_FILTERS = (
    {"Ano": "{year}", "Subtipo de delito": "Homicidio doloso"},
    {"Ano": "{year}", "Tipo de delito": FEMINICIDIO},
    {"Ano": "{year}", "Tipo de delito": SECUESTRO},
    {"Ano": "{year}", "Tipo de delito": EXTORSION},
)


def download_air(destination: Path, *, work_dir: Path) -> list[dict[str, object]]:
    networks = _scica_networks()
    work_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(_latest_network, code, name, work_dir): code for code, name in networks}
        for future in as_completed(futures):
            row = future.result()
            if row is not None:
                results.append(row)
    results.sort(key=lambda item: str(item["network_code"]))
    _write_dicts(destination, results)
    return results


def download_crime(
    destination: Path, *, year: int, raw_excerpt: Path | None = None
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    for template in CRIME_FILTERS:
        filters = {key: value.format(year=year) for key, value in template.items()}
        rows.extend(_datastore_all(filters))
    if raw_excerpt is not None and rows:
        _write_dicts(raw_excerpt, rows[:12])
    aggregated = aggregate_municipios(rows, year=year)
    _write_dicts(destination, aggregated)
    return aggregated, rows


def download_population(destination: Path, *, year: int) -> list[dict[str, object]]:
    payload = _get(CONAPO_POPULATION, timeout=180)
    text = payload.decode("utf-8-sig")
    published: list[dict[str, object]] = []
    for row in csv.DictReader(text.splitlines()):
        if str(row.get("ANO", "")).strip() != str(year):
            continue
        published.append(
            {
                "mun_code": int(row["CLAVE"]),
                "state_code": f"{int(row['CLAVE_ENT']):02d}",
                "state_name": row["NOM_ENT"].strip(),
                "mun_name": row["NOM_MUN"].strip(),
                "year": int(year),
                "population": int(round(float(row["POB_MIT_MUN"]))),
            }
        )
    published.sort(key=lambda item: int(item["mun_code"]))
    _write_dicts(destination, published)
    return published


def download_perception(destination: Path, *, pdf_path: Path) -> list[dict[str, object]]:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(_get(ENSU_PERCEPTION_PDF, timeout=120))
    text = _pdftotext(pdf_path)
    rows = parse_perception_text(text)
    _write_dicts(destination, rows)
    return rows


def download_catalog(destination: Path, *, pdf_path: Path) -> list[dict[str, object]]:
    import pdfplumber

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(_get(ENSU_CATALOG_PDF, timeout=120))
    collected: list[dict[str, object]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                collected.extend(municipalities_from_catalog_rows(table))
    # A city can continue on the next page; the page parser already
    # dedupes within a page. Deduplicate again across pages.
    unique: dict[tuple[str, int], dict[str, object]] = {}
    for row in collected:
        unique[(str(row["ensu_city"]), int(row["mun_code"]))] = row
    rows = sorted(unique.values(), key=lambda item: (str(item["ensu_city"]), int(item["mun_code"])))
    _write_dicts(destination, rows)
    return rows


def crime_month_profile(rows: list[dict[str, object]], *, year: int) -> dict[str, int]:
    """National month sums for intentional homicide, to see a partial year."""
    from aire_abierto.livability.safety import MONTHS

    totals = dict.fromkeys(MONTHS, 0)
    for row in rows:
        if str(row.get("Ano", "")).strip() != str(year):
            continue
        if str(row.get("Subtipo de delito", "")).strip() != "Homicidio doloso":
            continue
        for month in MONTHS:
            totals[month] += month_total({month: row.get(month, 0)})
    return totals


def _latest_network(code: str, name: str, work_dir: Path) -> dict[str, object] | None:
    years = _scica_years(code)
    for year in reversed(years[-4:]):
        path = work_dir / f"{code}-PM25-{year}.csv"
        try:
            _post_file(
                SCICA_HOURLY,
                {
                    "data[Exec][contaminante]": "PM25",
                    "data[Exec][red]": code,
                    "data[Exec][anio]": str(year),
                    "data[Exec][do_exec]": "1",
                    "data[Exec][get_csv]": "1",
                },
                path,
            )
        except OSError:
            continue
        if path.stat().st_size < 200:
            continue
        try:
            summary = annual_pm25_from_hourly(path, network_code=code, year=year)
        except ValueError:
            continue
        summary["network_name"] = name
        if summary["valid"]:
            return summary
    return None


def _scica_networks() -> list[tuple[str, str]]:
    import re

    body = _post(
        SCICA_NETWORKS,
        {"data[Exec][contaminante]": "PM25", "data[Exec][do_exec]": "0", "data[Exec][get_csv]": "0"},
    ).decode("utf-8", errors="replace")
    return re.findall(r'<option value="([^"]+)">([^<]+)</option>', body)


def _scica_years(code: str) -> list[int]:
    import re

    body = _post(
        SCICA_YEARS,
        {
            "data[Exec][contaminante]": "PM25",
            "data[Exec][red]": code,
            "data[Exec][do_exec]": "0",
            "data[Exec][get_csv]": "0",
        },
    ).decode("utf-8", errors="replace")
    return [int(year) for year in re.findall(r'value="(\d{4})"', body)]


def _datastore_all(filters: dict[str, str], *, page: int = 5000) -> list[dict[str, object]]:
    offset = 0
    collected: list[dict[str, object]] = []
    total = None
    while True:
        query = urllib.parse.urlencode(
            {
                "resource_id": SESNSP_RESOURCE,
                "limit": page,
                "offset": offset,
                "filters": json.dumps(filters, ensure_ascii=False),
            }
        )
        payload = json.loads(_get(f"{SESNSP_SEARCH}?{query}", timeout=120).decode("utf-8"))
        result = payload["result"]
        records = result.get("records") or []
        total = result.get("total", total)
        collected.extend(records)
        offset += len(records)
        if not records or (total is not None and offset >= int(total)):
            break
    return collected


def _pdftotext(path: Path) -> str:
    import subprocess

    completed = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
    )
    return completed.stdout.decode("utf-8", errors="replace")


def _post(url: str, fields: dict[str, str]) -> bytes:
    data = urllib.parse.urlencode(fields).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def _post_file(url: str, fields: dict[str, str], destination: Path) -> None:
    destination.write_bytes(_post(url, fields))


def _get(url: str, *, timeout: int) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Refresh public livability excerpts. Needs the network.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--year-crime", type=int, default=2025)
    parser.add_argument("--year-population", type=int, default=2025)
    parser.add_argument(
        "--only",
        choices=("all", "air", "crime", "population", "perception", "catalog"),
        default="all",
    )
    args = parser.parse_args(argv)
    out = args.out
    work = out / "_download"
    steps = {args.only} if args.only != "all" else {"air", "crime", "population", "perception", "catalog"}
    if "population" in steps:
        rows = download_population(out / "conapo_mun_2025.csv", year=args.year_population)
        print(f"population {args.year_population}: {len(rows)} municipalities")
    if "crime" in steps:
        aggregated, raw = download_crime(
            out / "sesnsp_municipio_2025.csv",
            year=args.year_crime,
            raw_excerpt=out / "sesnsp_raw_excerpt.csv",
        )
        lethal = sum(int(row["homicidio_doloso"]) + int(row["feminicidio"]) for row in aggregated)
        print(f"crime {args.year_crime}: {len(aggregated)} municipalities, lethal count {lethal}, raw rows {len(raw)}")
        print("homicidio doloso by month:", crime_month_profile(raw, year=args.year_crime))
    if "perception" in steps:
        rows = download_perception(out / "ensu_percepcion_2024q4.csv", pdf_path=work / "ensu2024_diciembre.pdf")
        print(f"perception: {len(rows)} rows")
    if "catalog" in steps:
        rows = download_catalog(out / "ensu_municipios.csv", pdf_path=work / "ensu2025_catalogo.pdf")
        print(f"catalog: {len(rows)} city-municipality rows, {len({row['ensu_city'] for row in rows})} cities")
    if "air" in steps:
        rows = download_air(out / "sinaica_pm25_annual.csv", work_dir=work / "scica")
        print(f"air: {len(rows)} networks with a valid annual mean")
    return 0


def _write_dicts(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames and not str(key).startswith("_"):
                fieldnames.append(str(key))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
