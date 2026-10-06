"""Tải mạng đường và landmark từ OpenStreetMap bằng osmnx. Owner: P1."""

from __future__ import annotations

from pathlib import Path

from src.config import REPO_ROOT


RAW_DIR = REPO_ROOT / "data" / "raw"


def fetch_road_network(
    cache_path: Path = RAW_DIR / "hcmc_drive.graphml",
    force: bool = False,
):
    """Tải mạng đường xe chạy trong 5 quận và lưu cache."""

    import osmnx as ox

    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if cache_path.exists() and not force:
        return ox.load_graphml(cache_path)

    # Bounding box bao phủ 5 quận mục tiêu.
    north = 10.825
    south = 10.745
    east = 106.735
    west = 106.650

    graph = ox.graph_from_bbox(
        (west, south, east, north),
        network_type="drive",
        simplify=True,
    )

    ox.save_graphml(graph, cache_path)

    return graph


def fetch_landmarks(
    cache_path: Path = RAW_DIR / "landmarks.geojson",
    force: bool = False,
):
    """Tải landmark từ OpenStreetMap và lưu cache."""

    import osmnx as ox

    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if cache_path.exists() and not force:
        return ox.features_from_bbox(
            (106.735, 10.745, 106.650, 10.825),
            tags={
                "amenity": True,
                "tourism": True,
                "leisure": True,
                "shop": True,
                "historic": True,
            },
        )

    tags = {
        "amenity": [
            "school",
            "hospital",
            "university",
            "marketplace",
            "library",
            "place_of_worship",
        ],
        "tourism": [
            "attraction",
            "museum",
            "gallery",
        ],
        "leisure": [
            "park",
            "garden",
            "sports_centre",
        ],
        "shop": [
            "mall",
        ],
        "historic": True,
    }

    landmarks = ox.features_from_bbox(
        (106.735, 10.745, 106.650, 10.825),
        tags=tags,
    )

    landmarks.to_file(cache_path, driver="GeoJSON")

    return landmarks