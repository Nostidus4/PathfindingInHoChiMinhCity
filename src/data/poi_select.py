"""Chọn POI từ dữ liệu OSM. Owner: P1.

Nhiệm vụ:
- Chọn ngã tư: node có degree >= 3 trên graph đường.
- Chọn landmark và snap vào node đường gần nhất.
- Cân bằng theo quận (>= 20 POI mỗi quận, tổng >= 100), loại trùng/quá gần nhau.
- Đặt tên ngã tư từ tên 2 đường giao nhau, ví dụ "Nguyễn Huệ x Lê Lợi".
- Gán district bằng data/districts.py.
"""

from __future__ import annotations

from src.models import POI


def select_intersections(osm_graph, min_degree: int = 3) -> list[POI]:
    """Các ngã tư (degree >= min_degree) nằm trong 5 quận."""
    raise NotImplementedError("TODO(P1)")


def snap_landmarks(landmarks, osm_graph) -> list[POI]:
    """Snap landmark vào node đường gần nhất, trả POI kind="landmark"."""
    raise NotImplementedError("TODO(P1)")


def name_intersection(osm_graph, node_id) -> str:
    """Tên ngã tư từ tên 2 đường giao nhau."""
    raise NotImplementedError("TODO(P1)")


def balance_by_district(pois: list[POI], per_district: int = 20, seed: int = 42) -> list[POI]:
    """Lấy mẫu cân bằng theo quận, có seed để tái lập."""
    raise NotImplementedError("TODO(P1)")
