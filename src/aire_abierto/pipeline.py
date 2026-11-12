"""Build the warehouse, the daily metrics, and the quality report."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

from aire_abierto.ingest import IngestError, acquire
from aire_abierto.parse import write_hourly_csv
from aire_abierto.paths import repo_root
from aire_abierto.publish import metro_rows, rank_rows, write_dicts
from aire_abierto.quality import assess
from aire_abierto.stations import load_stations
from aire_abierto.synthetic import SYNTHETIC_STATIONS
from aire_abierto.transform import build_daily_stations, open_warehouse, write_daily_csv


def run_pipeline(
    *,
    source: str,
    year: int,
    out_dir: Path,
    root: Path | None = None,
    as_of: date | None = None,
    refresh: bool = False,
) -> dict:
    root = root or repo_root()
    out_dir.mkdir(parents=True, exist_ok=True)
    as_of = as_of or date.today()
    acquired = acquire(source, year=year, root=root, work_dir=out_dir, refresh=refresh)
    hourly_path = out_dir / "_hourly.csv"
    row_count = write_hourly_csv(acquired.path, hourly_path)
    database = out_dir / "aire.duckdb"
    connection = open_warehouse(hourly_path, database)
    try:
        report = assess(
            connection,
            as_of=as_of,
            data_kind=acquired.data_kind,
            year=year if acquired.data_kind == "official_workbook" else None,
        )
        stations = load_stations()
        if acquired.data_kind == "synthetic":
            stations = {**stations, **SYNTHETIC_STATIONS}
        daily = build_daily_stations(connection, stations)
    finally:
        connection.close()

    write_daily_csv(daily, out_dir / "daily_station.csv")
    write_dicts(metro_rows(daily), out_dir / "daily_metro.csv")
    write_dicts(rank_rows(daily), out_dir / "station_rank.csv")
    quality_path = out_dir / "quality_report.json"
    quality_path.write_text(
        json.dumps(report.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "project": "aire-abierto",
        "data_kind": acquired.data_kind,
        "source_mode": acquired.source_mode,
        "year_requested": year,
        "url": acquired.url,
        "sha256": acquired.sha256,
        "retrieved_at": acquired.retrieved_at,
        "built_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "hourly_rows": row_count,
        "note_es": acquired.note_es,
        "note_en": acquired.note_en,
        "fallback_reason": acquired.fallback_reason,
        "norm": "NOM-172-SEMARNAT-2023",
        "particle_band_column": "A partir de enero de 2026",
        "not_official_index": True,
        "publisher": (
            "Secretaría de Medio Ambiente y Desarrollo Territorial de Jalisco (SEMADET), "
            "Sistema de Monitoreo Atmosférico de Jalisco (SIMAJ)"
            if acquired.data_kind != "synthetic"
            else "Aire abierto synthetic fallback"
        ),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"ok": report.ok, "manifest": manifest, "quality": report.as_dict(), "out_dir": str(out_dir)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build Guadalajara air-quality metrics from public SEMADET data."
    )
    parser.add_argument(
        "--source",
        choices=("auto", "live", "sample", "synthetic"),
        default="auto",
        help="live downloads the public workbook; sample uses the committed excerpt; "
        "synthetic is invented; auto tries live and falls back to the excerpt.",
    )
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--out", type=Path, default=None, help="Defaults to data/metrics.")
    parser.add_argument("--as-of", type=date.fromisoformat, default=None)
    parser.add_argument("--refresh", action="store_true", help="Download the workbook again.")
    args = parser.parse_args(argv)
    out_dir = args.out or (repo_root() / "data" / "metrics")
    try:
        result = run_pipeline(
            source=args.source,
            year=args.year,
            out_dir=out_dir,
            as_of=args.as_of,
            refresh=args.refresh,
        )
    except IngestError as exc:
        print(exc, file=sys.stderr)
        return 2
    manifest = result["manifest"]
    print(
        f"{manifest['data_kind']}: {manifest['hourly_rows']} hourly rows -> {result['out_dir']}"
    )
    if manifest["fallback_reason"]:
        print(f"fallback: {manifest['fallback_reason']}")
    for check in result["quality"]["checks"]:
        print(f"  [{check['status']}] {check['id']}: {check['detail_en']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
