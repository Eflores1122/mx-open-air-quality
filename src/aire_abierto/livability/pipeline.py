"""Build the livability mart from public excerpts or from invented rows."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

from aire_abierto.livability.air import semadet_annual_pm25
from aire_abierto.livability.mart import Bundle, assemble_mart, read_csv
from aire_abierto.livability.quality import assess
from aire_abierto.livability.synthetic import synthetic_bundle
from aire_abierto.offline import OfflineError
from aire_abierto.paths import repo_root


def samples_dir(root: Path) -> Path:
    return root / "data" / "livability" / "samples"


def reference_networks(root: Path) -> Path:
    return root / "data" / "livability" / "reference" / "networks.csv"


def run_livability(
    *,
    source: str,
    out_dir: Path,
    root: Path | None = None,
    as_of: date | None = None,
) -> dict:
    root = root or repo_root()
    out_dir.mkdir(parents=True, exist_ok=True)
    as_of = as_of or date.today()
    if source not in {"auto", "live", "sample", "synthetic"}:
        raise ValueError(f"Unknown source '{source}'.")
    fallback = None
    if source == "synthetic":
        bundle = synthetic_bundle()
        source_mode = "synthetic"
    else:
        sample_root = samples_dir(root)
        if source == "live":
            sample_root = _refresh(out_dir / "_live")
            source_mode = "live"
        elif source == "auto":
            try:
                sample_root = _refresh(out_dir / "_live")
                source_mode = "live"
            except (OSError, ValueError, RuntimeError) as exc:
                sample_root = samples_dir(root)
                source_mode = "sample"
                fallback = str(exc)
        else:
            source_mode = "sample"
        bundle = _load_sample(sample_root, root)
        if source_mode == "live":
            bundle.data_kind = "official_live"
    semadet_path = root / "data" / "metrics" / "daily_station.csv"
    if bundle.data_kind != "synthetic":
        bundle.semadet = semadet_annual_pm25(semadet_path)
    mart, bridge = assemble_mart(bundle)
    report = assess(mart, as_of=as_of, data_kind=bundle.data_kind, warnings=bundle.warnings)
    _write_dicts(mart, out_dir / "place_mart.csv")
    _write_dicts(bridge, out_dir / "place_municipalities.csv")
    (out_dir / "quality_report.json").write_text(
        json.dumps(report.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "project": "mx-livability",
        "package": "aire_abierto",
        "data_kind": bundle.data_kind,
        "source_mode": source_mode,
        "built_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "places": len(mart),
        "fallback_reason": fallback,
        "not_official_advice": True,
        "scoring": {
            "air_good_ugm3": 5,
            "air_poor_ugm3": 35,
            "safety_poor_per_100k": 80,
            "safety_basket": "homicidio_doloso + feminicidio",
            "rent_good_monthly_mxn": 2000,
            "rent_poor_monthly_mxn": 6000,
            "quality_weights": {"air": 0.40, "safety": 0.35, "perception": 0.25},
            "combined_weights": {"air": 0.30, "safety": 0.30, "perception": 0.20, "rent": 0.20},
        },
        "sources": _source_cards(),
        "note_es": (
            "Comparación cívica de aire, renta aproximada y seguridad. "
            "No es consejo oficial, ni médico, ni una evaluación de riesgo personal."
        ),
        "note_en": (
            "A civic comparison of air, approximate rent, and safety. "
            "It is not official advice, not medical advice, and not a personal risk assessment."
        ),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"ok": report.ok, "manifest": manifest, "quality": report.as_dict(), "out_dir": str(out_dir), "mart": mart}


def _load_sample(sample_root: Path, root: Path) -> Bundle:
    required = {
        "air": sample_root / "sinaica_pm25_annual.csv",
        "crime": sample_root / "sesnsp_municipio_2025.csv",
        "population": sample_root / "conapo_mun_2025.csv",
        "perception": sample_root / "ensu_percepcion_2024q4.csv",
        "catalog": sample_root / "ensu_municipios.csv",
        "rent": sample_root / "enigh_alquiler_imputado_2024.csv",
    }
    missing = [str(path) for path in required.values() if not path.is_file()]
    networks = reference_networks(root)
    if not networks.is_file():
        missing.append(str(networks))
    if missing:
        raise FileNotFoundError("Missing livability excerpts: " + ", ".join(missing))
    return Bundle(
        networks=read_csv(networks),
        air=read_csv(required["air"]),
        crime=read_csv(required["crime"]),
        population=read_csv(required["population"]),
        perception=read_csv(required["perception"]),
        catalog=read_csv(required["catalog"]),
        rent=read_csv(required["rent"]),
        data_kind="official_excerpt",
    )


def _refresh(destination: Path) -> Path:
    from aire_abierto.livability.download import main as download_main

    code = download_main(["--out", str(destination)])
    if code != 0:
        raise OSError("The public refresh failed.")
    return destination


def _source_cards() -> list[dict[str, str]]:
    return [
        {
            "id": "sinaica",
            "publisher": "Instituto Nacional de Ecología y Cambio Climático (INECC), SINAICA / SCICA",
            "url": "http://scica.inecc.gob.mx/exec/datadl",
            "vintage": "Latest validated PM2.5 year per network, mostly through 2022 or 2023",
            "license": "No SPDX license is stated on the download page. Attributed to INECC.",
        },
        {
            "id": "semadet",
            "publisher": "SEMADET, SIMAJ, Jalisco",
            "url": "https://aire.jalisco.gob.mx/reportes/BD_2025.xlsx",
            "vintage": "2025 hourly workbook, read by the existing Guadalajara pipeline",
            "license": "No SPDX license is stated. Attributed to SEMADET. Not mixed into the national score.",
        },
        {
            "id": "sesnsp",
            "publisher": "Secretariado Ejecutivo del Sistema Nacional de Seguridad Pública (SESNSP)",
            "url": "https://www.datos.gob.mx/dataset/incidencia_delictiva",
            "vintage": "Municipal nueva metodología, year used in the excerpt (2025 if that year is complete)",
            "license": (
                "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) on datos.gob.mx "
                "resource 57fbd692-3e5c-4b1b-8621-694cb3a33035. Attributed to SESNSP."
            ),
        },
        {
            "id": "conapo",
            "publisher": "CONAPO",
            "url": "https://www.datos.gob.mx/dataset/proyecciones-de-poblacion",
            "vintage": "Mid-year municipal population, same year as the crime counts",
            "license": (
                "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) on datos.gob.mx "
                "resource e9160552-769b-41ee-88d1-afc765552608 (pobproy_inddemo.csv). "
                "Attributed to CONAPO."
            ),
        },
        {
            "id": "ensu",
            "publisher": "INEGI, Encuesta Nacional de Seguridad Pública Urbana",
            "url": "https://www.inegi.org.mx/programas/ensu/",
            "vintage": "December 2024 perception; 2025 city-municipality catalog",
            "license": (
                "INEGI Términos de Libre Uso "
                "(https://www.inegi.org.mx/contenidos/inegi/doc/terminos_info.pdf). "
                "Attribution required. Not relicensed as CC by this project."
            ),
        },
        {
            "id": "enigh",
            "publisher": "INEGI, ENIGH 2024",
            "url": "https://www.inegi.org.mx/app/tabulados/interactivos/?pxq=Hogares_Hogares_11_861f5732-c3db-4614-be03-741f649d605c",
            "vintage": "2024, quarterly imputed rent by state",
            "license": (
                "INEGI Términos de Libre Uso "
                "(https://www.inegi.org.mx/contenidos/inegi/doc/terminos_info.pdf). "
                "Attribution required. The committed file is a transcription of the published table."
            ),
        },
    ]


def _write_dicts(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(str(key))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Mexico livability mart from public excerpts.")
    parser.add_argument("--source", choices=("auto", "live", "sample", "synthetic"), default="sample")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--as-of", type=date.fromisoformat, default=None)
    args = parser.parse_args(argv)
    out_dir = args.out or (repo_root() / "data" / "livability" / "metrics")
    try:
        result = run_livability(source=args.source, out_dir=out_dir, as_of=args.as_of)
    except OfflineError as exc:
        print(exc, file=sys.stderr)
        return 2
    manifest = result["manifest"]
    print(f"{manifest['data_kind']}: {manifest['places']} places -> {result['out_dir']}")
    if manifest["fallback_reason"]:
        print(f"fallback: {manifest['fallback_reason']}")
    for check in result["quality"]["checks"]:
        print(f"  [{check['status']}] {check['id']}: {check['detail_en']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
