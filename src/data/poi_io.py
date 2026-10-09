"""Đọc/ghi data/processed/pois.csv. Owner: P1."""

from __future__ import annotations

import csv
from pathlib import Path

from src.config import REPO_ROOT
from src.models import POI

DEFAULT_POIS_PATH = REPO_ROOT / "data" / "processed" / "pois.csv"

FIELDS = (
    "id",
    "name",
    "lat",
    "lon",
    "district",
    "kind",
)


def load_pois(path: Path = DEFAULT_POIS_PATH) -> list[POI]:
    """Đọc pois.csv -> list[POI]."""

    pois: list[POI] = []

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            pois.append(
                POI(
                    id=row["id"],
                    name=row["name"],
                    lat=float(row["lat"]),
                    lon=float(row["lon"]),
                    district=row["district"],
                    kind=row["kind"],
                )
            )

    return pois


def save_pois(
    pois: list[POI],
    path: Path = DEFAULT_POIS_PATH,
) -> None:
    """Ghi list[POI] -> pois.csv."""

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)

        writer.writeheader()

        for poi in pois:
            writer.writerow(
                {
                    "id": poi.id,
                    "name": poi.name,
                    "lat": poi.lat,
                    "lon": poi.lon,
                    "district": poi.district,
                    "kind": poi.kind,
                }
            )
