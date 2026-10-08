"""Tải mạng đường và landmark từ OpenStreetMap bằng osmnx. Owner: P1.

- Vùng tải = khung bao 5 quận (districts.bounding_box) nới thêm margin_m mỗi phía, để đường
  ở sát ranh giới không bị cắt cụt (POI vẫn chỉ chọn bên trong 5 quận).
- Có cache trong data/raw/; nếu cache không phủ đủ vùng cần tải thì tự tải lại.
- Cần `uv sync --group data`. Import osmnx BÊN TRONG hàm.
"""

from __future__ import annotations

from pathlib import Path

from src.config import REPO_ROOT
from src.data.districts import bounding_box

RAW_DIR = REPO_ROOT / "data" / "raw"

DEFAULT_MARGIN_M = 1000.0

# Tag landmark lấy từ OSM
LANDMARK_TAGS: dict[str, list[str] | bool] = {
    "amenity": ["school", "hospital", "university", "marketplace", "library", "place_of_worship"],
    "tourism": ["attraction", "museum", "gallery"],
    "leisure": ["park", "garden", "sports_centre"],
    "shop": ["mall"],
    "historic": True,
}

# Cột giữ lại khi lưu landmark ra GeoJSON (cột dạng list của osmnx không ghi được)
_LANDMARK_COLUMNS = ("name", "wikidata", "wikipedia", *LANDMARK_TAGS)


def _covers(osm_graph, bbox: tuple[float, float, float, float], tol_deg: float = 0.002) -> bool:
    """Cache có phủ đủ bbox (west, south, east, north) không, sai số ~200 m."""
    xs = [float(d["x"]) for _, d in osm_graph.nodes(data=True)]
    ys = [float(d["y"]) for _, d in osm_graph.nodes(data=True)]
    if not xs:
        return False
    west, south, east, north = bbox
    return (
        min(xs) <= west + tol_deg
        and min(ys) <= south + tol_deg
        and max(xs) >= east - tol_deg
        and max(ys) >= north - tol_deg
    )


def fetch_road_network(
    cache_path: Path = RAW_DIR / "hcmc_drive.graphml",
    force: bool = False,
    margin_m: float = DEFAULT_MARGIN_M,
):
    """Tải mạng đường xe chạy phủ 5 quận (nới margin_m) và lưu cache.

    Trả networkx.MultiDiGraph của osmnx.
    """

    import osmnx as ox

    bbox = bounding_box(margin_m)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if cache_path.exists() and not force:
        graph = ox.load_graphml(cache_path)
        if _covers(graph, bbox):
            return graph
        print(f"Cache {cache_path.name} không phủ đủ vùng cần tải, tải lại từ OSM...")

    graph = ox.graph_from_bbox(bbox, network_type="drive", simplify=True)
    ox.save_graphml(graph, cache_path)
    return graph


def fetch_landmarks(
    cache_path: Path = RAW_DIR / "landmarks.geojson",
    force: bool = False,
):
    """Tải landmark trong vùng 5 quận và lưu cache GeoJSON. Trả GeoDataFrame.

    Index giữ dạng của osmnx: (element, id), ví dụ ("way", 123456).
    """

    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if cache_path.exists() and not force:
        import geopandas as gpd

        gdf = gpd.read_file(cache_path)
        return gdf.set_index(["element", "id"])

    import osmnx as ox

    gdf = ox.features_from_bbox(bounding_box(), tags=LANDMARK_TAGS)
    keep = [c for c in _LANDMARK_COLUMNS if c in gdf.columns]
    gdf = gdf[[*keep, "geometry"]]
    gdf.reset_index().to_file(cache_path, driver="GeoJSON")
    return gdf
