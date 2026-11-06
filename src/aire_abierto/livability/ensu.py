"""ENSU perception of insecurity, from the published executive table.

The December 2024 presentation prints two numbers per city: September
and December. The figure used here is December. It is the share of
people 18 and older who said living in their city is unsafe. INEGI
prints it as a percentage. Margins of error in that presentation
average about 11 percent and can be much wider for a single city.
"""

from __future__ import annotations

import re

_ROW = re.compile(
    r"([A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 .,'’-]{1,}?)\s+"
    r"(\d+\.\d+)\s+(\d+\.\d+)\s+[^\d\s]{1,4}\s+(-?\d+\.\d+)"
)


def parse_perception_text(text: str, *, minimum_rows: int = 80) -> list[dict[str, object]]:
    """Parse the September–December 2024 city table from pdftotext output."""
    start = text.find("Septiembre Diciembre")
    if start < 0:
        raise ValueError("The ENSU text has no September–December table.")
    end = text.find("Cambio porcentual", start)
    chunk = text[start:] if end < 0 else text[start:end]
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for line in chunk.splitlines():
        for match in _ROW.finditer(line):
            name = re.sub(r"\s+", " ", match.group(1)).strip(" .")
            if name in seen:
                continue
            seen.add(name)
            rows.append(
                {
                    "ensu_city": name,
                    "september_pct": float(match.group(2)),
                    "december_pct": float(match.group(3)),
                    "change_pct": float(match.group(4)),
                    "period": "2024-12",
                    "comparison": "2024-09",
                }
            )
    if len(rows) < minimum_rows:
        raise ValueError(f"Expected at least {minimum_rows} ENSU rows, parsed {len(rows)}.")
    return rows


def municipalities_from_catalog_rows(table_rows: list[list[str | None]]) -> list[dict[str, object]]:
    """Forward-fill an ENSU city catalog table into city–municipality pairs.

    ``table_rows`` is what pdfplumber returns for one page: nine columns
    (city code, city, state code, state, municipality code, municipality,
    locality code, locality, CVEGEO). Headers are skipped. A locality
    without its own CVEGEO is rebuilt from the state, municipality, and
    locality codes when those three are present.
    """
    city_code = ""
    city_name = ""
    state_code = ""
    state_name = ""
    mun_code = ""
    mun_name = ""
    pairs: dict[tuple[str, int], dict[str, object]] = {}
    for raw in table_rows:
        cells = [_clean(cell) for cell in raw]
        if len(cells) < 9:
            cells = cells + [""] * (9 - len(cells))
        if _is_header(cells):
            continue
        if cells[0]:
            city_code = cells[0]
        if cells[1]:
            city_name = cells[1]
        if cells[2]:
            state_code = cells[2]
        if cells[3]:
            state_name = cells[3]
        if cells[4]:
            mun_code = cells[4]
        if cells[5]:
            mun_name = cells[5]
        loc_code = cells[6]
        cvegeo = cells[8]
        if not cvegeo and state_code and mun_code and loc_code and _digits(state_code) and _digits(mun_code):
            cvegeo = f"{int(state_code):02d}{int(mun_code):03d}{int(loc_code):04d}"
        if not cvegeo or not city_name or not _digits(cvegeo[:5]):
            continue
        code = int(cvegeo[:5])
        key = (city_name, code)
        pairs[key] = {
            "ensu_city": city_name,
            "ensu_city_code": city_code,
            "state_code": f"{int(cvegeo[:2]):02d}",
            "state_name": state_name,
            "mun_code": code,
            "mun_name": mun_name,
            "cvegeo_example": cvegeo,
        }
    published = list(pairs.values())
    published.sort(key=lambda item: (str(item["ensu_city"]), int(item["mun_code"])))
    return published


def _clean(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\n", " ").split())


def _digits(value: str) -> bool:
    return value.isdigit()


def _is_header(cells: list[str]) -> bool:
    joined = " ".join(cells).lower()
    return "cvegeo" in joined or "clave" == cells[0].lower() or "área urbana" in joined or "area urbana" in joined
