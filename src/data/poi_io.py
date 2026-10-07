"""Đọc/ghi data/processed/pois.csv. Owner: P1.

Cột CSV: id, name, lat, lon, district, kind (khớp dataclass models.POI).
"""

from __future__ import annotations

from pathlib import Path

from src.config import REPO_ROOT
from src.models import POI

DEFAULT_POIS_PATH = REPO_ROOT / "data" / "processed" / "pois.csv"


def load_pois(path: Path = DEFAULT_POIS_PATH) -> list[POI]:
    """Đọc pois.csv -> list[POI]."""
    raise NotImplementedError("TODO(P1)")


def save_pois(pois: list[POI], path: Path = DEFAULT_POIS_PATH) -> None:
    """Ghi list[POI] -> pois.csv."""
    raise NotImplementedError("TODO(P1)")
