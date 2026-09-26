"""Xây đồ thị POI từ mạng đường OSM. Owner: P2.

Nhiệm vụ build_graph(pois, osm_graph, k):
- Với mỗi POI, nối tới k POI gần nhất (k ≈ 6-8 theo proposal) bằng đường ngắn nhất trên mạng OSM.
- Lọc cạnh mà đường đi xuyên qua POI khác (để cạnh là "trực tiếp").
- Áp one-way từ OSM (chỉ tạo chiều đi được).
- Lưu length_m, road_type, district, lanes, geometry (polyline thật) vào RoadSegment.
Cần `uv sync --group data` (osm_graph là networkx graph của osmnx).
"""

from __future__ import annotations

from src.graph.graph import Graph
from src.models import POI


def build_graph(pois: list[POI], osm_graph, k: int = 6) -> Graph:
    """Tạo Graph nối mỗi POI với k POI gần nhất."""
    raise NotImplementedError("TODO(P2)")
