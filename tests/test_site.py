import csv
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from aire_abierto.livability.scoring import combine
from aire_abierto.livability.webexport import export_site
from aire_abierto.paths import repo_root

ROOT = repo_root()
SITE = ROOT / "site" / "data"


def test_committed_site_export_matches_the_mart(tmp_path: Path):
    fresh = tmp_path / "site"
    result = export_site(
        ROOT / "data" / "livability" / "metrics",
        ROOT / "data" / "livability" / "reference" / "place_points.csv",
        fresh,
    )
    assert result["places"] == 152
    assert result["points"] == 90
    assert result["parquet_rows"] == 152
    committed = json.loads((SITE / "place_mart.json").read_text(encoding="utf-8"))
    exported = json.loads((fresh / "place_mart.json").read_text(encoding="utf-8"))
    assert exported == committed
    saltillo = next(row for row in committed if row["place_id"] == "city:saltillo")
    zacatecas = next(row for row in committed if row["place_id"] == "city:zacatecas")
    assert saltillo["lethal_per_100k"] == 1.6015
    assert zacatecas["state_name"] == "Zacatecas"
    assert zacatecas["enigh_imputed_rent_monthly_approx_mxn"] == 1886.0
    one_station = [row for row in committed if row["air_stations_valid"] == 1]
    with_air = [row for row in committed if row["air_pm25_median_ugm3"] is not None]
    assert len(with_air) == 39
    assert len(one_station) == 27


def test_place_pins_name_a_geonames_locality_and_skip_la_laguna():
    path = ROOT / "data" / "livability" / "reference" / "place_points.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert len(rows) == 90
    assert "La Laguna" not in {row["place_name"] for row in rows}
    merida = next(row for row in rows if row["place_id"] == "city:merida")
    assert merida["geoname_id"] == "3523349"
    assert merida["lat"] == "20.967"
    juarez = next(row for row in rows if row["place_id"] == "city:juarez")
    assert juarez["geoname_id"] == "4013708"
    geo = json.loads((SITE / "mexico_states.geojson").read_text(encoding="utf-8"))
    codes = [feature["properties"]["state_code"] for feature in geo["features"]]
    assert codes == [f"{number:02d}" for number in range(1, 33)]
    capital = next(feature for feature in geo["features"] if feature["properties"]["state_code"] == "09")
    assert capital["properties"]["state_name"] == "Ciudad de México"
    assert capital["properties"]["source_name"] == "Distrito Federal"


def test_browser_weights_match_the_python_score(tmp_path: Path):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    places = json.loads((SITE / "place_mart.json").read_text(encoding="utf-8"))
    wanted = {"city:merida", "city:tijuana", "city:saltillo", "city:juarez"}
    sample = [row for row in places if row["place_id"] in wanted]
    weights = {"air": 0.4, "safety": 0.35, "perception": 0.25, "rent": 0.0}
    expected = {}
    for row in sample:
        components = {
            "air": row["score_air"],
            "safety": row["score_safety"],
            "perception": row["score_perception"],
            "rent": row["score_rent"],
        }
        score, _used = combine(components, weights, minimum=2)
        expected[row["place_id"]] = None if score is None else round(score, 4)
    script = r"""
const score = require("./site/score.js");
const places = JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"));
const weights = {air: 0.4, safety: 0.35, perception: 0.25, rent: 0};
const out = {};
for (const row of places) {
  const result = score.combine({
    air: row.score_air,
    safety: row.score_safety,
    perception: row.score_perception,
    rent: row.score_rent,
  }, weights, 2);
  out[row.place_id] = result.score === null ? null : Math.round(result.score * 10000) / 10000;
}
process.stdout.write(JSON.stringify(out));
"""
    payload = tmp_path / "score-sample.json"
    payload.write_text(json.dumps(sample), encoding="utf-8")
    completed = subprocess.run(
        [node, "-e", script, str(payload)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(completed.stdout) == expected


def test_pages_workflow_publishes_the_site_from_actions():
    workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
    assert "actions/upload-pages-artifact@" in workflow
    assert "actions/deploy-pages@" in workflow
    assert "pages: write" in workflow
    assert "id-token: write" in workflow
    assert "workflow_dispatch" in workflow
    assert "branches: [main]" in workflow
    assert "path: site" in workflow
