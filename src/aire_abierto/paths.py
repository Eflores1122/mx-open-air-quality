"""Repository paths. Works from a checkout and from an editable install."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "pyproject.toml").is_file() and (candidate / "src").is_dir():
            return candidate
    return Path.cwd()


def sample_csv(root: Path | None = None) -> Path:
    return (root or repo_root()) / "data" / "samples" / "simaj_hourly_2025-05-01_2025-05-14.csv"


def station_catalog(root: Path | None = None) -> Path:
    return (root or repo_root()) / "data" / "reference" / "simaj_stations.csv"
