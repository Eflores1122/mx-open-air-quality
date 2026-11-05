"""Fetch the public SEMADET workbook, or select an offline stand-in.

The live file is the annual workbook SEMADET publishes for direct download.
No account and no API key. If that download fails, ``auto`` uses the
committed excerpt of the same public file. ``synthetic`` never touches the
network. This module does not scrape pages behind a login.
"""

from __future__ import annotations

import hashlib
import shutil
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from aire_abierto.paths import sample_csv
from aire_abierto.synthetic import write_synthetic_csv

WORKBOOK_URL = "https://aire.jalisco.gob.mx/reportes/BD_{year}.xlsx"
USER_AGENT = "aire-abierto/0.1 (civic open-data project; public SEMADET workbook)"


class IngestError(RuntimeError):
    pass


@dataclass(frozen=True)
class Acquisition:
    path: Path
    data_kind: str
    source_mode: str
    url: str | None
    year: int | None
    sha256: str
    retrieved_at: str
    note_es: str
    note_en: str
    fallback_reason: str | None = None


def acquire(
    source: str,
    *,
    year: int,
    root: Path,
    work_dir: Path,
    refresh: bool = False,
) -> Acquisition:
    if source not in {"auto", "live", "sample", "synthetic"}:
        raise IngestError(f"Unknown source '{source}'.")
    work_dir.mkdir(parents=True, exist_ok=True)
    if source == "synthetic":
        return _synthetic(work_dir)
    if source == "sample":
        return _sample(root, year)
    try:
        return _live(year=year, root=root, refresh=refresh)
    except IngestError as exc:
        if source == "live":
            raise
        excerpt = _sample(root, year)
        return Acquisition(
            path=excerpt.path,
            data_kind=excerpt.data_kind,
            source_mode="auto",
            url=excerpt.url,
            year=year,
            sha256=excerpt.sha256,
            retrieved_at=excerpt.retrieved_at,
            note_es=excerpt.note_es,
            note_en=excerpt.note_en,
            fallback_reason=str(exc),
        )


def _live(*, year: int, root: Path, refresh: bool) -> Acquisition:
    url = WORKBOOK_URL.format(year=year)
    destination = root / "data" / "raw" / f"BD_{year}.xlsx"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not (destination.is_file() and destination.stat().st_size > 1_000_000 and not refresh):
        _download(url, destination)
    if destination.read_bytes()[:2] != b"PK":
        raise IngestError(f"The download from {url} is not an Excel workbook.")
    return Acquisition(
        path=destination,
        data_kind="official_workbook",
        source_mode="live",
        url=url,
        year=year,
        sha256=sha256(destination),
        retrieved_at=_now(),
        note_es=(
            "Archivo horario público de SEMADET para el SIMAJ, zona "
            f"metropolitana de Guadalajara, año {year}. No es un feed de hoy."
        ),
        note_en=(
            f"Public SEMADET hourly workbook for the Guadalajara SIMAJ network, "
            f"{year}. This is not today's feed."
        ),
    )


def _sample(root: Path, year: int) -> Acquisition:
    path = sample_csv(root)
    if not path.is_file():
        raise IngestError(f"Committed public excerpt is missing: {path}")
    return Acquisition(
        path=path,
        data_kind="official_excerpt",
        source_mode="sample",
        url=WORKBOOK_URL.format(year=2025),
        year=year,
        sha256=sha256(path),
        retrieved_at=_now(),
        note_es=(
            "Extracto público sin modificar del 1 al 14 de mayo de 2025, "
            "tomado del archivo horario de SEMADET. No es el año completo "
            "ni un dato inventado."
        ),
        note_en=(
            "Unmodified public excerpt, 1–14 May 2025, cut from the SEMADET "
            "hourly workbook. It is not the full year and it is not invented."
        ),
    )


def _synthetic(work_dir: Path) -> Acquisition:
    path = work_dir / "synthetic_hourly.csv"
    write_synthetic_csv(path)
    return Acquisition(
        path=path,
        data_kind="synthetic",
        source_mode="synthetic",
        url=None,
        year=None,
        sha256=sha256(path),
        retrieved_at=_now(),
        note_es=(
            "Datos inventados con el mismo esquema, para pruebas y para "
            "cuando el archivo público no se puede descargar. No describen "
            "el aire de ninguna ciudad."
        ),
        note_en=(
            "Invented rows in the same schema, for tests and for when the "
            "public file cannot be downloaded. They do not describe the air "
            "in any city."
        ),
    )


def _download(url: str, destination: Path) -> None:
    temporary = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                raise IngestError(f"HTTP {status} while downloading {url}")
            with temporary.open("wb") as handle:
                shutil.copyfileobj(response, handle)
    except urllib.error.URLError as exc:
        temporary.unlink(missing_ok=True)
        raise IngestError(f"Could not download {url}: {exc}") from exc
    except TimeoutError as exc:
        temporary.unlink(missing_ok=True)
        raise IngestError(f"Timed out downloading {url}") from exc
    temporary.replace(destination)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
