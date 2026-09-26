"""Ranh giới 5 quận cũ (tự vẽ polygon) và gán quận cho một toạ độ. Owner: P1.

Nhiệm vụ:
- DISTRICT_POLYGONS: dict tên quận -> list (lat, lon) các đỉnh polygon (tự vẽ, thuần Python).
- assign_district(lat, lon): trả tên quận chứa điểm, hoặc None nếu ngoài 5 quận.
- Dùng thuật toán ray casting (point-in-polygon) thuần Python, KHÔNG dùng shapely.
"""

from __future__ import annotations

DISTRICTS: tuple[str, ...] = ("Quan 1", "Quan 3", "Quan 5", "Binh Thanh", "Phu Nhuan")

# TODO(P1): vẽ polygon (lat, lon) cho từng quận, ví dụ bằng geojson.io rồi dán vào đây.
DISTRICT_POLYGONS: dict[str, list[tuple[float, float]]] = {name: [] for name in DISTRICTS}


def point_in_polygon(lat: float, lon: float, polygon: list[tuple[float, float]]) -> bool:
    """Ray casting: True nếu (lat, lon) nằm trong polygon."""
    raise NotImplementedError("TODO(P1)")


def assign_district(lat: float, lon: float) -> str | None:
    """Tên quận chứa (lat, lon), None nếu nằm ngoài cả 5 quận."""
    raise NotImplementedError("TODO(P1)")
