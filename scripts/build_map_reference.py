"""Build the map reference from public geometry. Not part of the mart.

Reads a GeoNames cities5000 dump and the Click That Hood Mexico state
polygons, then writes:

- data/livability/reference/place_points.csv
- site/data/mexico_states.geojson

The city pin is one GeoNames locality, matched inside the right state.
It is not the polygon of the ENSU city. La Laguna is left without a pin
because it crosses Coahuila and Durango.
"""

from __future__ import annotations

import argparse
import csv
import json
import unicodedata
import zipfile
from pathlib import Path

# GeoNames admin1 codes are not INEGI codes. Names are from admin1CodesASCII.
GEONAMES_ADMIN = {
    "01": "aguascalientes",
    "02": "baja california",
    "03": "baja california sur",
    "04": "campeche",
    "05": "chiapas",
    "06": "chihuahua",
    "07": "coahuila",
    "08": "colima",
    "09": "ciudad de mexico",
    "10": "durango",
    "11": "guanajuato",
    "12": "guerrero",
    "13": "hidalgo",
    "14": "jalisco",
    "15": "mexico",
    "16": "michoacan",
    "17": "morelos",
    "18": "nayarit",
    "19": "nuevo leon",
    "20": "oaxaca",
    "21": "puebla",
    "22": "queretaro",
    "23": "quintana roo",
    "24": "san luis potosi",
    "25": "sinaloa",
    "26": "sonora",
    "27": "tabasco",
    "28": "tamaulipas",
    "29": "tlaxcala",
    "30": "veracruz",
    "31": "yucatan",
    "32": "zacatecas",
}

# Longer official names to the GeoNames locality, used only when the
# ENSU name is not itself a GeoNames name in that state.
ALIASES = {
    "juarez": "ciudad juarez",
    "heroica puebla de zaragoza": "puebla",
    "oaxaca de juarez": "oaxaca",
    "san francisco de campeche": "campeche",
    "tlaxcala de xicohtencatl": "tlaxcala",
    "chilpancingo de los bravo": "chilpancingo",
    "culiacan rosales": "culiacan",
    "toluca de lerdo": "toluca",
    "general escobedo": "ciudad general escobedo",
    "xalapa": "xalapa de enriquez",
    "los cabos": "san jose del cabo",
    "la magdalena contreras": "magdalena contreras",
    "queretaro": "santiago de queretaro",
    "durango": "victoria de durango",
}

# Click That Hood still labels the capital as Distrito Federal.
STATE_CODE_BY_OUTLINE = {
    "aguascalientes": "01",
    "baja california": "02",
    "baja california sur": "03",
    "campeche": "04",
    "coahuila de zaragoza": "05",
    "colima": "06",
    "chiapas": "07",
    "chihuahua": "08",
    "distrito federal": "09",
    "ciudad de mexico": "09",
    "durango": "10",
    "guanajuato": "11",
    "guerrero": "12",
    "hidalgo": "13",
    "jalisco": "14",
    "mexico": "15",
    "michoacan de ocampo": "16",
    "morelos": "17",
    "nayarit": "18",
    "nuevo leon": "19",
    "oaxaca": "20",
    "puebla": "21",
    "queretaro": "22",
    "quintana roo": "23",
    "san luis potosi": "24",
    "sinaloa": "25",
    "sonora": "26",
    "tabasco": "27",
    "tamaulipas": "28",
    "tlaxcala": "29",
    "veracruz de ignacio de la llave": "30",
    "yucatan": "31",
    "zacatecas": "32",
}

CURRENT_STATE_NAME = {
    "09": "Ciudad de México",
}


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("’", "'")
    for ch in ",.-/":
        text = text.replace(ch, " ")
    return " ".join(text.split())


def state_key(name: str) -> str:
    text = norm(name)
    if " / " in name or " / " in text:
        return ""
    if text.startswith("ciudad de mexico"):
        return "ciudad de mexico"
    if text == "mexico":
        return "mexico"
    if text.startswith("baja california sur"):
        return "baja california sur"
    if text.startswith("baja california"):
        return "baja california"
    if text.startswith("coahuila"):
        return "coahuila"
    if text.startswith("michoacan"):
        return "michoacan"
    if text.startswith("veracruz"):
        return "veracruz"
    if text.startswith("nuevo leon"):
        return "nuevo leon"
    if text.startswith("san luis"):
        return "san luis potosi"
    if text.startswith("quintana"):
        return "quintana roo"
    return text


def load_geonames(path: Path) -> list[dict[str, object]]:
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            name = next(item for item in archive.namelist() if item.endswith(".txt"))
            raw = archive.read(name).decode("utf-8")
    else:
        raw = path.read_text(encoding="utf-8")
    places: list[dict[str, object]] = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) < 15 or parts[8] != "MX":
            continue
        places.append(
            {
                "id": parts[0],
                "name": parts[1],
                "ascii": parts[2],
                "alts": [item for item in parts[3].split(",") if item],
                "lat": float(parts[4]),
                "lon": float(parts[5]),
                "fcode": parts[7],
                "admin1": parts[10].zfill(2),
                "pop": int(parts[14] or 0),
            }
        )
    return places


def names_of(place: dict[str, object]) -> set[str]:
    found = {norm(str(place["name"])), norm(str(place["ascii"]))}
    for alt in place["alts"]:
        found.add(norm(str(alt)))
    return found


def rank(place: dict[str, object]) -> tuple[int, int, int]:
    preferred = {"PPLC": 0, "PPLA": 1, "PPLA2": 2, "PPLA3": 3, "PPL": 4, "PPLX": 5}
    return (-int(place["pop"]), preferred.get(str(place["fcode"]), 9), str(place["name"]))


def match_city(city: dict[str, str], places: list[dict[str, object]]) -> dict[str, object] | None:
    short = city["place_name"].replace(", CDMX", "").strip()
    key = norm(short)
    if city["place_name"] == "La Laguna":
        return None
    preferred_state = "tamaulipas" if city["place_name"] == "Tampico" else state_key(city["state_name"])
    if not preferred_state:
        return None
    target = ALIASES.get(key, key)
    pool = [place for place in places if GEONAMES_ADMIN.get(str(place["admin1"])) == preferred_state]
    exact = [place for place in pool if target in names_of(place)]
    if not exact and target != key:
        exact = [place for place in pool if key in names_of(place)]
    if not exact:
        exact = [
            place
            for place in pool
            if any(name.startswith(target) or target.startswith(name) for name in names_of(place) if len(name) > 4)
        ]
    if not exact:
        return None
    exact.sort(key=rank)
    chosen = exact[0]
    note_es, note_en = _notes(city["place_name"], str(chosen["name"]), str(chosen["id"]))
    return {
        "place_id": city["place_id"],
        "place_name": city["place_name"],
        "lat": round(float(chosen["lat"]), 5),
        "lon": round(float(chosen["lon"]), 5),
        "geoname_id": chosen["id"],
        "geoname_name": chosen["name"],
        "geoname_admin1": chosen["admin1"],
        "note_es": note_es,
        "note_en": note_en,
    }


def _notes(place_name: str, geoname: str, geoname_id: str) -> tuple[str, str]:
    base_es = (
        f"El punto es la localidad {geoname} (GeoNames {geoname_id}), no el polígono de la ciudad ENSU."
    )
    base_en = (
        f"The pin is the locality {geoname} (GeoNames {geoname_id}), not the polygon of the ENSU city."
    )
    if place_name == "Los Cabos":
        base_es += (
            " El catálogo ENSU nombra San José del Cabo como localidad cabecera."
            " Cabo San Lucas es otra localidad del mismo municipio."
        )
        base_en += (
            " The ENSU catalog names San José del Cabo as the head locality."
            " Cabo San Lucas is another locality in the same municipality."
        )
    if place_name == "Tampico":
        base_es += " La ciudad ENSU también incluye municipios de Veracruz. El punto es Tampico, Tamaulipas."
        base_en += " The ENSU city also includes municipalities in Veracruz. The pin is Tampico, Tamaulipas."
    if place_name == "Atizapán de Zaragoza":
        base_es += " GeoNames publica la localidad como Ciudad López Mateos."
        base_en += " GeoNames publishes the locality as Ciudad López Mateos."
    return base_es, base_en


def rdp(points: list[list[float]], epsilon: float) -> list[list[float]]:
    if len(points) < 3:
        return points

    def distance(point: list[float], start: list[float], end: list[float]) -> float:
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        if dx == 0 and dy == 0:
            return ((point[0] - start[0]) ** 2 + (point[1] - start[1]) ** 2) ** 0.5
        t = ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        px = start[0] + t * dx
        py = start[1] + t * dy
        return ((point[0] - px) ** 2 + (point[1] - py) ** 2) ** 0.5

    pivot = max(range(1, len(points) - 1), key=lambda index: distance(points[index], points[0], points[-1]))
    if distance(points[pivot], points[0], points[-1]) > epsilon:
        left = rdp(points[: pivot + 1], epsilon)
        right = rdp(points[pivot:], epsilon)
        return left[:-1] + right
    return [points[0], points[-1]]


def simplify_ring(ring: list[list[float]], epsilon: float) -> list[list[float]]:
    simplified = rdp(ring, epsilon)
    rounded = [[round(point[0], 3), round(point[1], 3)] for point in simplified]
    if len(rounded) < 4:
        return []
    if rounded[0] != rounded[-1]:
        rounded.append(rounded[0])
    return rounded


def simplify_geometry(geometry: dict, epsilon: float) -> dict | None:
    kind = geometry["type"]
    if kind == "Polygon":
        rings = [simplify_ring(ring, epsilon) for ring in geometry["coordinates"]]
        rings = [ring for ring in rings if ring]
        if not rings:
            return None
        return {"type": "Polygon", "coordinates": rings}
    if kind == "MultiPolygon":
        polygons = []
        for polygon in geometry["coordinates"]:
            rings = [simplify_ring(ring, epsilon) for ring in polygon]
            rings = [ring for ring in rings if ring]
            if rings:
                polygons.append(rings)
        if not polygons:
            return None
        return {"type": "MultiPolygon", "coordinates": polygons}
    raise ValueError(f"Unsupported geometry {kind}")


def simplify_states(source: Path, destination: Path, epsilon: float) -> None:
    raw = json.loads(source.read_text(encoding="utf-8"))
    features = []
    for feature in raw["features"]:
        source_name = str(feature["properties"]["name"])
        code = STATE_CODE_BY_OUTLINE.get(norm(source_name))
        if not code:
            raise SystemExit(f"No state code for outline {source_name}")
        geometry = simplify_geometry(feature["geometry"], epsilon)
        if geometry is None:
            raise SystemExit(f"Geometry disappeared for {source_name}")
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "state_code": code,
                    "state_name": CURRENT_STATE_NAME.get(code, source_name),
                    "source_name": source_name,
                },
                "geometry": geometry,
            }
        )
    features.sort(key=lambda item: item["properties"]["state_code"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {"type": "FeatureCollection", "features": features}
    destination.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"states {len(features)} -> {destination} ({destination.stat().st_size} bytes)")


def write_points(mart: Path, geonames: Path, destination: Path) -> None:
    places = load_geonames(geonames)
    cities = [row for row in csv.DictReader(mart.open(encoding="utf-8")) if row["place_type"] == "city"]
    matched = []
    missing = []
    for city in cities:
        found = match_city(city, places)
        if found is None:
            missing.append(city["place_name"])
            continue
        if not (14 <= float(found["lat"]) <= 33 and -119 <= float(found["lon"]) <= -86):
            raise SystemExit(f"Point outside Mexico: {found}")
        matched.append(found)
    if missing != ["La Laguna"]:
        raise SystemExit(f"Unexpected places without a pin: {missing}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "place_id",
        "place_name",
        "lat",
        "lon",
        "geoname_id",
        "geoname_name",
        "geoname_admin1",
        "note_es",
        "note_en",
    ]
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in matched:
            writer.writerow(row)
    renamed = [
        row
        for row in matched
        if norm(row["place_name"].replace(", CDMX", "")) != norm(str(row["geoname_name"]))
    ]
    print(f"points {len(matched)} -> {destination}")
    print("name differs:")
    for row in renamed:
        print(f"  {row['place_name']} -> {row['geoname_name']} ({row['lat']}, {row['lon']})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build map pins and simplified state outlines.")
    parser.add_argument("--geonames", type=Path, required=True)
    parser.add_argument("--states", type=Path, required=True)
    parser.add_argument("--mart", type=Path, required=True)
    parser.add_argument("--points", type=Path, required=True)
    parser.add_argument("--geojson", type=Path, required=True)
    parser.add_argument("--epsilon", type=float, default=0.02)
    args = parser.parse_args()
    write_points(args.mart, args.geonames, args.points)
    simplify_states(args.states, args.geojson, args.epsilon)


if __name__ == "__main__":
    main()
