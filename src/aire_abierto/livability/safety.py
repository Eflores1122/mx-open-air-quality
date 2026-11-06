"""SESNSP municipal counts for a small, named basket of crimes.

The open file is the municipal incidencia delictiva of the Secretariado
Ejecutivo del Sistema Nacional de Seguridad Pública, nueva metodología.
Each row is a crime type and modality, with twelve month columns.

The basket used for the rate is intentional homicide plus feminicide.
Those two are closer to comparable across states than robbery or
extortion, which move with how a fiscalía records them. Kidnapping and
extortion are still summed and published. They are not inside the score.

Counts are victim-investigation records, not a census of harm, and not
a forecast of personal risk.
"""

from __future__ import annotations

MONTHS = (
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
)

# Tipo / subtipo strings as the datos.gob.mx datastore spells them.
HOMICIDIO_DOLOSO = "Homicidio doloso"
FEMINICIDIO = "Feminicidio"
SECUESTRO = "Secuestro"
EXTORSION = "Extorsión"


def month_total(row: dict[str, object]) -> int:
    total = 0
    for month in MONTHS:
        total += _int_cell(row.get(month))
    return total


def aggregate_municipios(rows: list[dict[str, object]], *, year: int) -> list[dict[str, object]]:
    """Sum the basket to one row per municipality for a single year."""
    grouped: dict[int, dict[str, object]] = {}
    for row in rows:
        if _year(row) != year:
            continue
        code = _mun_code(row)
        if code is None:
            continue
        item = grouped.get(code)
        if item is None:
            item = {
                "mun_code": code,
                "state_code": f"{int(_text(row, 'Clave_Ent')):02d}",
                "state_name": _text(row, "Entidad").strip(),
                "mun_name": _text(row, "Municipio").strip(),
                "year": year,
                "homicidio_doloso": 0,
                "feminicidio": 0,
                "secuestro": 0,
                "extorsion": 0,
            }
            grouped[code] = item
        count = month_total(row)
        kind = _classify(row)
        if kind is None:
            continue
        item[kind] = int(item[kind]) + count
    published = list(grouped.values())
    published.sort(key=lambda item: int(item["mun_code"]))
    return published


def lethal_count(row: dict[str, object]) -> int:
    return int(row["homicidio_doloso"]) + int(row["feminicidio"])


def _classify(row: dict[str, object]) -> str | None:
    subtype = _text(row, "Subtipo de delito").strip()
    kind = _text(row, "Tipo de delito").strip()
    if subtype == HOMICIDIO_DOLOSO:
        return "homicidio_doloso"
    if kind == FEMINICIDIO or subtype == FEMINICIDIO:
        return "feminicidio"
    if kind == SECUESTRO or subtype == SECUESTRO:
        return "secuestro"
    if kind == EXTORSION or subtype == EXTORSION:
        return "extorsion"
    return None


def _year(row: dict[str, object]) -> int:
    raw = row.get("Ano", row.get("Año"))
    return int(str(raw).strip())


def _mun_code(row: dict[str, object]) -> int | None:
    raw = row.get("Cve. Municipio", row.get("Cve_Municipio"))
    if raw is None or str(raw).strip() == "":
        return None
    return int(float(str(raw).strip()))


def _text(row: dict[str, object], key: str) -> str:
    value = row.get(key, "")
    return "" if value is None else str(value)


def _int_cell(value: object) -> int:
    if value is None:
        return 0
    text = str(value).strip()
    if text == "":
        return 0
    return int(float(text))
