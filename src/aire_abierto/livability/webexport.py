"""Write the static JSON and Parquet the site reads.

The files are the committed mart, with empty cells as null and numbers
as numbers. Coordinates stay out of this file: the map joins
``place_points.csv`` on its own, and that join is not a measurement
from SINAICA, SESNSP, or ENIGH.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path

import duckdb

from aire_abierto.paths import repo_root

NUMERIC = {
    "air_year",
    "air_pm25_median_ugm3",
    "air_pm25_worst_ugm3",
    "air_stations_valid",
    "air_stations_in_file",
    "semadet_year",
    "semadet_pm25_median_ugm3",
    "semadet_stations_valid",
    "safety_year",
    "safety_population",
    "safety_coverage",
    "homicidio_doloso",
    "feminicidio",
    "secuestro",
    "extorsion",
    "lethal_per_100k",
    "secuestro_per_100k",
    "extorsion_per_100k",
    "perception_insecurity_pct",
    "rent_year",
    "enigh_imputed_rent_quarterly_mxn",
    "enigh_imputed_rent_monthly_approx_mxn",
    "score_air",
    "score_safety",
    "score_perception",
    "score_rent",
    "score_quality",
    "score_combined",
}


def coerce(key: str, value: str) -> object:
    text = (value or "").strip()
    if text == "":
        return None
    if key not in NUMERIC:
        return text
    number = float(text)
    if number.is_integer() and key not in {
        "air_pm25_median_ugm3",
        "air_pm25_worst_ugm3",
        "semadet_pm25_median_ugm3",
        "safety_coverage",
        "lethal_per_100k",
        "secuestro_per_100k",
        "extorsion_per_100k",
        "perception_insecurity_pct",
        "enigh_imputed_rent_quarterly_mxn",
        "enigh_imputed_rent_monthly_approx_mxn",
        "score_air",
        "score_safety",
        "score_perception",
        "score_rent",
        "score_quality",
        "score_combined",
    }:
        return int(number)
    return number


def read_mart(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [{key: coerce(key, value) for key, value in row.items()} for row in csv.DictReader(handle)]


def read_points(path: Path) -> list[dict[str, object]]:
    rows = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "place_id": row["place_id"],
                    "lat": float(row["lat"]),
                    "lon": float(row["lon"]),
                    "geoname_id": row["geoname_id"],
                    "geoname_name": row["geoname_name"],
                    "note_es": row["note_es"],
                    "note_en": row["note_en"],
                }
            )
    return rows


def export_site(metrics: Path, points: Path, destination: Path) -> dict[str, int]:
    destination.mkdir(parents=True, exist_ok=True)
    mart_path = metrics / "place_mart.csv"
    places = read_mart(mart_path)
    (destination / "place_mart.json").write_text(
        json.dumps(places, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    for name in ("manifest.json", "quality_report.json"):
        shutil.copyfile(metrics / name, destination / name)
    point_rows = read_points(points)
    (destination / "place_points.json").write_text(
        json.dumps(point_rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    parquet = destination / "place_mart.parquet"
    if parquet.exists():
        parquet.unlink()
    json_path = str(destination / "place_mart.json")
    connection = duckdb.connect()
    try:
        connection.execute(
            f"COPY (SELECT * FROM read_json_auto('{json_path}')) TO '{parquet}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        count = connection.execute(f"SELECT count(*) FROM read_parquet('{parquet}')").fetchone()
    finally:
        connection.close()
    return {"places": len(places), "points": len(point_rows), "parquet_rows": int(count[0])}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export the livability mart for the static site.")
    parser.add_argument("--metrics", type=Path, default=None)
    parser.add_argument("--points", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    root = repo_root()
    metrics = args.metrics or (root / "data" / "livability" / "metrics")
    points = args.points or (root / "data" / "livability" / "reference" / "place_points.csv")
    destination = args.out or (root / "site" / "data")
    result = export_site(metrics, points, destination)
    print(
        f"{result['places']} places, {result['points']} pins, {result['parquet_rows']} parquet rows -> {destination}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
