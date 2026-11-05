"""Parse SEMADET hourly workbooks and the committed public excerpt.

Invalid cells stay empty and keep the flag SEMADET already published
(IO, ND, IR, IF, IC, and any other non-numeric token). Nothing is imputed.
"""

from __future__ import annotations

import csv
from collections.abc import Iterator
from datetime import date, datetime, timedelta
from pathlib import Path

HOURLY_COLUMNS = (
    "station_code",
    "observed_at",
    "o3_ppm",
    "no2_ppm",
    "so2_ppm",
    "co_ppm",
    "pm10_ugm3",
    "pm25_ugm3",
    "o3_flag",
    "no2_flag",
    "so2_flag",
    "co_flag",
    "pm10_flag",
    "pm25_flag",
)

_HEADER_MAP = {
    "STATION": "station",
    "ESTACION": "station",
    "ESTACIÓN": "station",
    "DATE": "date",
    "FECHA": "date",
    "HOUR": "hour",
    "HORA": "hour",
    "O3": "o3",
    "NO2": "no2",
    "SO2": "so2",
    "CO": "co",
    "PM10": "pm10",
    "PM2.5": "pm25",
    "PM25": "pm25",
    "PM2_5": "pm25",
}

_FLAG_TOKENS = {
    "IO",
    "ND",
    "IR",
    "IF",
    "IC",
    "SD",
    "NA",
    "NAN",
    "NULL",
    "NONE",
    "N/A",
    "MANT",
    "MANT.",
    "OFFSCAN",
    "-",
    "--",
}


def parse_measurement(value: object) -> tuple[float | None, str | None]:
    if value is None:
        return None, None
    if isinstance(value, bool):
        return None, None
    if isinstance(value, (int, float)):
        number = float(value)
        if number != number:  # NaN
            return None, "ND"
        return number, None
    text = str(value).strip()
    if text == "":
        return None, None
    token = text.upper().replace(" ", "")
    if token in _FLAG_TOKENS:
        return None, token
    normalized = text.replace(",", ".")
    try:
        return float(normalized), None
    except ValueError:
        return None, token[:24]


def parse_timestamp(date_value: object, hour_value: object) -> datetime | None:
    base = _coerce_datetime(date_value)
    if base is None:
        return None
    base = base.replace(minute=0, second=0, microsecond=0)
    hour = _coerce_hour(hour_value)
    if hour is None:
        return base
    if hour == 24:
        if base.hour != 0:
            return base
        return base + timedelta(days=1)
    if base.hour == hour:
        return base
    if base.hour == 0:
        return base.replace(hour=hour)
    return base


def write_hourly_csv(source: Path, destination: Path) -> int:
    destination.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HOURLY_COLUMNS)
        writer.writeheader()
        for row in iter_hourly_rows(source):
            writer.writerow(row)
            count += 1
    return count


def iter_hourly_rows(source: Path) -> Iterator[dict[str, str]]:
    suffix = source.suffix.lower()
    if suffix == ".csv":
        yield from _rows_from_csv(source)
        return
    if suffix == ".xlsx":
        yield from _rows_from_xlsx(source)
        return
    raise ValueError(f"Unsupported air-quality file: {source.name}")


def _rows_from_csv(path: Path) -> Iterator[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return
        mapping = _map_headers(reader.fieldnames)
        for raw in reader:
            yield from _emit(raw, mapping)


def _rows_from_xlsx(path: Path) -> Iterator[dict[str, str]]:
    from openpyxl import load_workbook

    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = workbook[workbook.sheetnames[0]]
        rows = sheet.iter_rows(values_only=True)
        header = next(rows, None)
        if header is None:
            return
        labels = ["" if cell is None else str(cell) for cell in header]
        mapping = _map_headers(labels)
        for values in rows:
            raw = {
                labels[index]: values[index] if index < len(values) else None
                for index in range(len(labels))
            }
            normalized = _normalize(raw, mapping)
            if normalized is not None:
                yield normalized
    finally:
        workbook.close()


def _emit(raw: dict[object, object], mapping: dict[str, str]) -> Iterator[dict[str, str]]:
    normalized = _normalize(raw, mapping)
    if normalized is not None:
        yield normalized


def _normalize(raw: dict[object, object], mapping: dict[str, str]) -> dict[str, str] | None:
    by_logical = {logical: raw.get(original) for logical, original in mapping.items()}
    station = str(by_logical.get("station") or "").strip().upper()
    observed = parse_timestamp(by_logical.get("date"), by_logical.get("hour"))
    if not station or observed is None:
        return None
    measurements = {
        key: parse_measurement(by_logical.get(key))
        for key in ("o3", "no2", "so2", "co", "pm10", "pm25")
    }
    return {
        "station_code": station,
        "observed_at": observed.strftime("%Y-%m-%dT%H:%M:%S"),
        "o3_ppm": _num(measurements["o3"][0]),
        "no2_ppm": _num(measurements["no2"][0]),
        "so2_ppm": _num(measurements["so2"][0]),
        "co_ppm": _num(measurements["co"][0]),
        "pm10_ugm3": _num(measurements["pm10"][0]),
        "pm25_ugm3": _num(measurements["pm25"][0]),
        "o3_flag": measurements["o3"][1] or "",
        "no2_flag": measurements["no2"][1] or "",
        "so2_flag": measurements["so2"][1] or "",
        "co_flag": measurements["co"][1] or "",
        "pm10_flag": measurements["pm10"][1] or "",
        "pm25_flag": measurements["pm25"][1] or "",
    }


def _map_headers(headers: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for header in headers:
        key = header.strip().upper().replace(" ", "")
        logical = _HEADER_MAP.get(key)
        if logical and logical not in mapping:
            mapping[logical] = header
    missing = {"station", "date"} - set(mapping)
    if missing:
        raise ValueError(f"Air-quality file is missing columns: {sorted(missing)}")
    return mapping


def _num(value: float | None) -> str:
    if value is None:
        return ""
    return format(value, ".10g")


def _coerce_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _coerce_hour(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != int(number):
        return None
    hour = int(number)
    if hour < 0 or hour > 24:
        return None
    return hour
